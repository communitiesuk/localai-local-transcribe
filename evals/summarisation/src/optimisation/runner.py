from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

import dspy
import orjson
import tiktoken
from datasets import load_dataset
from dspy.evaluate import Evaluate

from common.database.postgres_models import DialogueEntry, HallucinationType
from common.llm.adapters.llm_constants import MAX_COMPLETION_TOKENS as MAX_TOKENS
from common.llm.adapters.llm_constants import TEMPERATURE
from common.settings import get_settings
from evals.summarisation.prompts import DIMENSIONS
from evals.summarisation.src.common import (
    AppConfig,
    DialogExample,
    DialogSummary,
    EvalRecord,
    GenerationConfig,
    MetricResult,
    call_llm_judge_parallel,
    write_jsonl,
)
from evals.summarisation.src.hallucination.types import HallucinationInput
from evals.summarisation.src.summarizer import generate_summary

_DIALOGSUM_SPEAKER_RE = re.compile(r"^#([^#]+)#:\s*(.+)$")

logger = logging.getLogger(__name__)


class _RunSummary(TypedDict):
    run_id: str
    split: str
    n: int
    overall: float | None
    metrics: dict[str, dict[str, float]]
    latency_ms: dict[str, int]
    review: dict[str, float | int]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _elapsed_ms(start_s: float, end_s: float) -> int:
    return int(round((end_s - start_s) * 1000))


def _prepare_run_paths(cfg: AppConfig, run_id: str) -> tuple[Path, Path, Path, Path]:
    out_dir = Path(cfg.run.output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir, out_dir / "results.jsonl", out_dir / "summary.json", out_dir / "hallucination_inputs.json"


def _load_data_pairs(cfg: AppConfig, *, split: str, limit: int | None) -> list[DialogExample]:
    ds = load_dataset(cfg.dataset.name, cfg.dataset.config)
    rows = ds[split]
    if limit is not None:
        rows = rows.select(range(min(limit, len(rows))))

    return [
        DialogExample(
            example_id=str(row.get("id", i)),
            dialogue=row[cfg.dataset.dialogue_field],
            reference_summary=row.get(cfg.dataset.reference_summary_field),
        )
        for i, row in enumerate(rows)
    ]


def _to_dspy_devset(examples: list[DialogExample]) -> list[dspy.Example]:
    return [
        dspy.Example(
            example_id=ex.example_id,
            dialogue=ex.dialogue,
            reference_summary=ex.reference_summary,
        ).with_inputs("dialogue")
        for ex in examples
    ]


def _trigger_review(
    metrics_out: dict[str, MetricResult],
    *,
    threshold: int = 4,
) -> tuple[bool, list[str]]:
    failing = [name for name, res in metrics_out.items() if name.startswith("rubric_") and res.score < threshold]
    return bool(failing), failing


def _dialogue_to_entries(dialogue: str) -> list[DialogueEntry]:
    """Converts dialogsum-format dialogue string to DialogueEntry objects."""
    entries: list[DialogueEntry] = []
    for i, raw_line in enumerate(dialogue.splitlines()):
        line = raw_line.strip()
        if not line:
            continue
        match = _DIALOGSUM_SPEAKER_RE.match(line)
        speaker = match.group(1) if match else "Speaker"
        text = match.group(2) if match else line
        entries.append({"speaker": speaker, "text": text, "start_time": float(i), "end_time": float(i + 1)})
    return entries


def _maybe_flush_records(results_path: Path, records: list[EvalRecord], *, flush_every: int) -> None:
    if len(records) >= flush_every:
        write_jsonl(results_path, (r.model_dump(by_alias=True) for r in records))
        records.clear()


def _p50(values: list[int]) -> int:
    if not values:
        return 0
    values_sorted = sorted(values)
    return int(values_sorted[len(values_sorted) // 2])


def run_eval(
    cfg: AppConfig,
    *,
    split: str,
    limit: int | None,
    prompt_version: str,
) -> tuple[str, Path, Path, Path]:
    run_id = str(uuid.uuid4())
    _, results_path, summary_path, hallucination_inputs_path = _prepare_run_paths(cfg, run_id)

    examples = _load_data_pairs(cfg, split=split, limit=limit)
    devset = _to_dspy_devset(examples)

    model_name = get_settings().FAST_LLM_MODEL_NAME
    template_name = cfg.prompts.summarizer_template_name
    hallucination_enabled = cfg.hallucination.enabled

    # Use tiktoken for token evaluation
    tokenizer_model = get_settings().FAST_LLM_MODEL_NAME
    enc = tiktoken.encoding_for_model(tokenizer_model)

    # Accumulators and status trackers
    records: list[EvalRecord] = []
    hallucination_inputs: list[HallucinationInput] = []
    summarize_ms_values: list[int] = []
    judge_ms_values: list[int] = []
    review_flags: list[bool] = []
    metric_scores: dict[str, list[float]] = defaultdict(list)

    # Establish event loop to drive async functions from the synchronous evaluator
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    class _Program:
        def __call__(self, *, dialogue: str) -> dspy.Prediction:
            entries = _dialogue_to_entries(dialogue)
            t0 = time.perf_counter()
            generated = loop.run_until_complete(generate_summary(entries, template_name))
            summarize_ms_values.append(_elapsed_ms(t0, time.perf_counter()))

            candidate = DialogSummary(
                summary=generated.text,
                model=model_name,
                prompt_version=prompt_version,
                generation_config=GenerationConfig(temperature=TEMPERATURE, max_tokens=MAX_TOKENS),
            )

            token_count = len(enc.encode(generated.text))
            logger.info("[TokenUsage] Generated summary token count: %s", token_count)
            metric_scores["token_usage"].append(float(token_count))

            return dspy.Prediction(
                summary=generated.text,
                candidate=candidate,
                hallucinations=generated.hallucinations,
                total_claims=generated.total_claims,
            )

    program = _Program()

    def _metric(gold: DialogExample, pred: dspy.Prediction) -> float:
        ex = DialogExample(
            example_id=str(gold.example_id),
            dialogue=str(gold.dialogue),
            reference_summary=getattr(gold, "reference_summary", None),
        )

        t_j0 = time.perf_counter()
        # Evaluate rubric dimensions via the parallel LLM judge
        rubric_evaluation = loop.run_until_complete(
            call_llm_judge_parallel(
                summary_id=ex.example_id,
                transcript_ref=str(ex.example_id),
                transcript_text=ex.dialogue,
                summary_text=pred.summary,
                dimensions=list(DIMENSIONS.keys()),
            )
        )
        judge_ms = _elapsed_ms(t_j0, time.perf_counter())
        judge_ms_values.append(judge_ms)

        metrics_out = {}
        for dim, result in rubric_evaluation["dimensions"].items():
            raw_score = int(result["score"])
            # Use the original 1‑5 score directly per user request
            metrics_out[f"rubric_{dim}"] = MetricResult(score=raw_score, reason=result["rationale"])

        for name, res in metrics_out.items():
            metric_scores[name].append(res.score)

        candidate = pred.candidate
        needs_review, review_reasons = _trigger_review(metrics_out, threshold=4)
        review_flags.append(needs_review)

        records.append(
            EvalRecord(
                run_id=run_id,
                timestamp=_utc_now(),
                example=ex,
                candidate=candidate,
                metrics=metrics_out,
                needs_review=needs_review,
                review_reasons=review_reasons,
                latency_ms={
                    "summarize": summarize_ms_values[-1] if summarize_ms_values else 0,
                    "judge": judge_ms,
                },
                error=None,
                token_usage=int(metric_scores["token_usage"][-1]) if metric_scores.get("token_usage") else None,
            )
        )
        _maybe_flush_records(results_path, records, flush_every=25)

        if hallucination_enabled:
            uncited_claims = [
                h.hallucination_text
                for h in pred.hallucinations
                if h.hallucination_type == HallucinationType.FACTUAL_FABRICATION
            ]
            hallucination_inputs.append(
                HallucinationInput(
                    example_id=str(gold.example_id),
                    hypothesis_model=model_name,
                    summary_html=candidate.summary,
                    uncited_claims=uncited_claims,
                    total_claims=pred.total_claims,
                )
            )

        rubric_vals = [res.score for name, res in metrics_out.items() if name.startswith("rubric_")]
        if rubric_vals:
            return float(sum(rubric_vals) / len(rubric_vals))
        return 0.0

    evaluator = Evaluate(devset=devset, num_threads=1, display_progress=True)
    evaluator(program, metric=_metric)

    if records:
        write_jsonl(results_path, (r.model_dump(by_alias=True) for r in records))

    # Construct execution summaries
    metrics_summary: dict[str, dict[str, float]] = {
        name: {"mean": float(sum(vals) / len(vals)) if vals else 0.0}
        for name, vals in metric_scores.items()
        if name != "token_usage"
    }

    if "token_usage" in metric_scores:
        total_token = sum(metric_scores["token_usage"])
        metrics_summary["token_usage"] = {"total": total_token}

    rubric_scores = [v["mean"] for k, v in metrics_summary.items() if k.startswith("rubric_")]
    overall = float(sum(rubric_scores) / len(rubric_scores)) if rubric_scores else None

    review_flagged_count = sum(review_flags)
    review_rate = review_flagged_count / len(review_flags) if review_flags else 0.0

    summary: _RunSummary = {
        "run_id": run_id,
        "split": split,
        "n": len(devset),
        "overall": overall,
        "metrics": metrics_summary,
        "latency_ms": {
            "summarize_p50": _p50(summarize_ms_values),
            "judge_p50": _p50(judge_ms_values),
        },
        "review": {
            "count": review_flagged_count,
            "rate": review_rate,
        },
    }

    summary_path.write_bytes(orjson.dumps(summary, option=orjson.OPT_INDENT_2))
    hallucination_inputs_path.write_bytes(
        orjson.dumps([h.model_dump() for h in hallucination_inputs], option=orjson.OPT_INDENT_2)
    )

    try:
        loop.close()
    except Exception as e:
        logger.debug("Failed to close evaluation event loop safely: %s", e)

    return run_id, results_path, summary_path, hallucination_inputs_path
