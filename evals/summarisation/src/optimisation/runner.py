from __future__ import annotations

import asyncio
import re
import time
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

import dspy
import orjson
from datasets import load_dataset
from dspy.evaluate import Evaluate
from pydantic import BaseModel, ConfigDict, Field

from common.database.postgres_models import DialogueEntry, HallucinationType
from common.settings import get_settings
from evals.summarisation.prompts.judge import build_system_prompt, build_user_message
from evals.summarisation.src.common import (
    AppConfig,
    DialogExample,
    DialogSummary,
    DialogSummaryMetric,
    EvalRecord,
    GenerationConfig,
    MetricResult,
    build_azure_apim_adapter,
    build_metrics,
    write_jsonl,
)
from evals.summarisation.src.hallucination.types import HallucinationInput
from evals.summarisation.src.summarizer import generate_summary


class DimensionEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="The name of the evaluation dimension (e.g. clarity, correctness).")
    score: int = Field(description="The score assigned to this dimension.", ge=1, le=5)
    rationale: str = Field(description="The rationale behind the score.")


class RubricEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimensions: list[DimensionEvaluation] = Field(description="A list of evaluation dimension scores and rationales.")


_DIALOGSUM_SPEAKER_RE = re.compile(r"^#([^#]+)#:\s*(.+)$")


async def call_llm_judge(system: str, user: str) -> dict:
    """
    Direct call to the LLM judge using the project's standard settings.
    This avoids polluting the summarizer service with evaluation logic.
    """

    adapter = build_azure_apim_adapter()

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    response = await adapter.structured_chat(messages, RubricEvaluation)

    dimensions_dict = {}
    for item in response.dimensions:
        dimensions_dict[item.name] = {"score": item.score, "rationale": item.rationale}

    return {"dimensions": dimensions_dict}


class _RunSummary(TypedDict):
    run_id: str
    split: str
    n: int
    overall: float | None
    metrics: dict[str, dict[str, float]]
    latency_ms: dict[str, int]


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


def _evaluate_metrics(
    *,
    metrics: Iterable[DialogSummaryMetric],
    example: DialogExample,
    prediction: dspy.Prediction,
) -> dict[str, MetricResult]:
    results = {}
    for m in metrics:
        res = m.evaluate(example=example, prediction=prediction)
        results[m.name] = res
    return results


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
    metrics = build_metrics(cfg)
    hallucination_enabled = cfg.hallucination.enabled

    records: list[EvalRecord] = []
    hallucination_inputs: list[HallucinationInput] = []
    summarize_ms_values: list[int] = []
    judge_ms_values: list[int] = []
    metric_names = [m.name for m in metrics]
    metric_scores: dict[str, list[float]] = {name: [] for name in metric_names}

    class _Program:
        def __call__(self, *, dialogue: str) -> dspy.Prediction:
            entries = _dialogue_to_entries(dialogue)
            t0 = time.perf_counter()
            generated = asyncio.run(generate_summary(entries, template_name))
            summarize_ms_values.append(_elapsed_ms(t0, time.perf_counter()))
            candidate = DialogSummary(
                summary=generated.text,
                model=model_name,
                prompt_version=prompt_version,
                generation_config=GenerationConfig(temperature=1, max_tokens=1024),
            )
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
        metrics_out = _evaluate_metrics(metrics=metrics, example=ex, prediction=pred)

        sys_prompt = build_system_prompt()
        user_msg = build_user_message(
            summary_id=ex.example_id,
            transcript_ref=str(ex.example_id),
            transcript_text=ex.dialogue,
            summary_text=pred.summary,
        )

        rubric_evaluation = asyncio.run(call_llm_judge(sys_prompt, user_msg))

        for dim, result in rubric_evaluation["dimensions"].items():
            metrics_out[f"rubric_{dim}"] = MetricResult(score=int(result["score"]), reason=result["rationale"])

        judge_ms = _elapsed_ms(t_j0, time.perf_counter())
        judge_ms_values.append(judge_ms)

        for name, res in metrics_out.items():
            if name not in metric_scores:
                metric_scores[name] = []
            metric_scores[name].append(res.score)

        candidate = pred.candidate
        records.append(
            EvalRecord(
                run_id=run_id,
                timestamp=_utc_now(),
                example=ex,
                candidate=candidate,
                metrics=metrics_out,
                latency_ms={
                    "summarize": summarize_ms_values[-1] if summarize_ms_values else 0,
                    "judge": judge_ms,
                },
                error=None,
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

        if metric_names:
            return float(sum(metrics_out[n].score for n in metric_names) / len(metric_names))
        rubric_vals = [res.score for name, res in metrics_out.items() if name.startswith("rubric_")]
        if rubric_vals:
            return float(sum(rubric_vals) / len(rubric_vals))
        return 0.0

    evaluator = Evaluate(devset=devset, num_threads=1, display_progress=True, display_table=5, provide_traceback=True)
    evaluator(program, metric=_metric)

    if records:
        write_jsonl(results_path, [r.model_dump(by_alias=True) for r in records])

    metrics_summary: dict[str, dict[str, float]] = {
        name: {"mean": float(int(sum(vals) / len(vals)) if vals else 0)} for name, vals in metric_scores.items()
    }
    rubric_scores = [v["mean"] for k, v in metrics_summary.items() if k.startswith("rubric_")]
    summary: _RunSummary = {
        "run_id": run_id,
        "split": split,
        "n": len(devset),
        "overall": float(sum(rubric_scores) / len(rubric_scores)) if rubric_scores else None,
        "metrics": metrics_summary,
        "latency_ms": {
            "summarize_p50": _p50(summarize_ms_values),
            "judge_p50": _p50(judge_ms_values),
        },
    }

    summary_path.write_bytes(orjson.dumps(summary, option=orjson.OPT_INDENT_2))
    hallucination_inputs_path.write_bytes(
        orjson.dumps([h.model_dump() for h in hallucination_inputs], option=orjson.OPT_INDENT_2)
    )
    return run_id, results_path, summary_path, hallucination_inputs_path
