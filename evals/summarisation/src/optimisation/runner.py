from __future__ import annotations

import asyncio
import logging
import re
import threading
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import dspy
import orjson
import tiktoken
from datasets import load_dataset
from dspy.evaluate import Evaluate

from common.database.postgres_models import DialogueEntry
from common.llm.adapters.llm_constants import MAX_COMPLETION_TOKENS as MAX_TOKENS
from common.llm.adapters.llm_constants import TEMPERATURE
from common.settings import get_settings
from evals.summarisation.prompts import DIMENSIONS
from evals.summarisation.src.common import (
    AppConfig,
    DialogExample,
    DialogSummary,
    EvalRecord,
    EvalRunState,
    GenerationConfig,
    MetricResult,
    RunSummary,
    call_llm_judge_parallel,
    judge_transcript_text,
    write_jsonl,
)
from evals.summarisation.src.common.metric import judged_dimensions
from evals.summarisation.src.hallucination.types import HallucinationInput
from evals.summarisation.src.optimisation.data.loader import load_local_examples
from evals.summarisation.src.summarizer import generate_summary

_DIALOGSUM_SPEAKER_RE = re.compile(r"^#([^#]+)#:\s*(.+)$")

_thread_local = threading.local()


def _run_async(coro: Any) -> Any:
    if not hasattr(_thread_local, "loop") or _thread_local.loop.is_closed():
        _thread_local.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_thread_local.loop)
    return _thread_local.loop.run_until_complete(coro)


logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _elapsed_ms(start_s: float, end_s: float) -> int:
    return int(round((end_s - start_s) * 1000))


def _p50(values: list[int]) -> int:
    if not values:
        return 0
    values_sorted = sorted(values)
    return int(values_sorted[len(values_sorted) // 2])


def _dialogue_to_entries(dialogue: str) -> list[DialogueEntry]:
    entries: list[DialogueEntry] = []
    for i, raw_line in enumerate(dialogue.splitlines()):
        line = raw_line.strip()
        if not line:
            continue

        match = _DIALOGSUM_SPEAKER_RE.match(line)
        speaker = match.group(1) if match else "Speaker"
        text = match.group(2) if match else line

        entries.append(
            {
                "speaker": speaker,
                "text": text,
                "start_time": float(i),
                "end_time": float(i + 1),
            }
        )
    return entries


def judge_transcript_from_dialogue(dialogue: str) -> str:
    """Render a raw dataset dialogue for the judge with the citation step's entry numbering.

    The summariser is handed the dialogue as ``DialogueEntry`` objects and cites them by index, so
    the judge has to be shown the same entries under the same numbers to check a ``[n]`` marker.
    """
    return judge_transcript_text(_dialogue_to_entries(dialogue))


def prepare_run_paths(output_dir: str | Path, run_id: str) -> tuple[Path, Path, Path]:
    out_dir = Path(output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    return (
        out_dir / "results.jsonl",
        out_dir / "summary.json",
        out_dir / "hallucination_inputs.json",
    )


def _configured_input_dir(cfg: AppConfig) -> Path:
    if cfg.run.input_dir is None:
        msg = "run.input_dir must be set when dataset.source is 'local_dir'"
        raise ValueError(msg)
    return Path(cfg.run.input_dir)


def load_dspy_devset(
    cfg: AppConfig,
    split: str,
    limit: int | None,
    dataset_path: Path | None = None,
) -> list[dspy.Example]:
    """Builds the devset from the configured source; ``dataset_path`` overrides ``run.input_dir``."""
    if cfg.dataset.source == "local_dir":
        input_dir = dataset_path if dataset_path is not None else _configured_input_dir(cfg)
        # Entries travel with the example so the summariser gets the transcript as generated.
        return [
            dspy.Example(
                example_id=ex.example_id,
                dialogue=ex.dialogue,
                dialogue_entries=ex.dialogue_entries,
                reference_summary=ex.reference_summary,
            ).with_inputs("dialogue", "dialogue_entries")
            for ex in load_local_examples(input_dir, limit)
        ]

    ds = load_dataset(cfg.dataset.name, cfg.dataset.config)
    rows = ds[split]
    if limit is not None:
        rows = rows.select(range(min(limit, len(rows))))

    examples = [
        DialogExample(
            example_id=str(row.get("id", i)),
            dialogue=row[cfg.dataset.dialogue_field],
            reference_summary=row.get(cfg.dataset.reference_summary_field),
        )
        for i, row in enumerate(rows)
    ]
    return [
        dspy.Example(
            example_id=ex.example_id,
            dialogue=ex.dialogue,
            reference_summary=ex.reference_summary,
        ).with_inputs("dialogue")
        for ex in examples
    ]


class EvalRun:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        split: str,
        limit: int | None,
        prompt_version: str,
        dataset_path: Path | None = None,
    ) -> None:
        self.cfg = cfg
        self.split = split
        self.limit = limit
        self.prompt_version = prompt_version
        self.dataset_path = dataset_path

        settings = get_settings()
        self.model_name: str = settings.FAST_LLM_MODEL_NAME
        self.template_name: str | None = cfg.prompts.summarizer_template_name
        self.hallucination_enabled: bool = cfg.hallucination.enabled
        # Resolved once up front so an unknown template name fails before any LLM call is made.
        self.dimensions: list[str] = judged_dimensions(DIMENSIONS, self.template_name)
        self.skipped_dimensions: list[str] = [d for d in DIMENSIONS if d not in self.dimensions]
        self.enc: tiktoken.Encoding = tiktoken.encoding_for_model(self.model_name)

        self.run_id: str = ""
        self.results_path: Path = Path()
        self.summary_path: Path = Path()
        self.hallucination_inputs_path: Path = Path()
        self.devset: list[dspy.Example] = []
        self.state: EvalRunState = EvalRunState()

    def _build_program(self) -> dspy.Module:
        run = self

        class _Program(dspy.Module):
            def forward(self, dialogue: str, dialogue_entries: list[DialogueEntry] | None = None) -> dspy.Prediction:
                entries = dialogue_entries if dialogue_entries else _dialogue_to_entries(dialogue)

                t0 = time.perf_counter()

                # Check satisfies both mypy and pre-commit security rules
                generated = _run_async(generate_summary(entries, run.template_name))
                run.state.summarize_ms_values.append(_elapsed_ms(t0, time.perf_counter()))

                candidate = DialogSummary(
                    summary=generated.text,
                    model=run.model_name,
                    prompt_version=run.prompt_version,
                    generation_config=GenerationConfig(
                        temperature=TEMPERATURE,
                        max_tokens=MAX_TOKENS,
                    ),
                )

                token_count = len(run.enc.encode(generated.text))
                logger.info("[TokenUsage] Generated summary token count: %s", token_count)
                run.state.metric_scores["token_usage"].append(float(token_count))

                return dspy.Prediction(
                    summary=generated.text,
                    candidate=candidate,
                    hallucinations=generated.hallucinations,
                    total_claims=generated.total_claims,
                )

        return _Program()

    def _build_metric(self) -> Callable[[dspy.Example, dspy.Prediction], float]:
        run = self

        def _metric(gold: dspy.Example, pred: dspy.Prediction) -> float:
            ex = DialogExample(
                example_id=str(gold.example_id),
                dialogue=str(gold.dialogue),
                dialogue_entries=getattr(gold, "dialogue_entries", None),
                reference_summary=getattr(gold, "reference_summary", None),
            )

            # Numbered once and reused for the record, so a rationale citing `[n]` can be resolved
            # against the transcript stored beside it.
            judge_transcript = (
                judge_transcript_text(ex.dialogue_entries)
                if ex.dialogue_entries
                else judge_transcript_from_dialogue(ex.dialogue)
            )

            t_j0 = time.perf_counter()
            rubric_evaluation = _run_async(
                call_llm_judge_parallel(
                    summary_id=ex.example_id,
                    transcript_ref=str(ex.example_id),
                    transcript_text=judge_transcript,
                    summary_text=pred.summary,
                    dimensions=run.dimensions,
                )
            )
            run.state.judge_ms_values.append(_elapsed_ms(t_j0, time.perf_counter()))

            metrics_out = _collect_rubric_metrics(rubric_evaluation)
            for name, res in metrics_out.items():
                run.state.metric_scores[name].append(res.score)

            if run.hallucination_enabled:
                uncited_claims = [h.hallucination_text for h in pred.hallucinations]
                run.state.hallucination_inputs.append(
                    HallucinationInput(
                        example_id=ex.example_id,
                        hypothesis_model=run.model_name,
                        summary_html=pred.candidate.summary,
                        uncited_claims=uncited_claims,
                        total_claims=pred.total_claims,
                    )
                )

            record = EvalRecord(
                run_id=run.run_id,
                example_id=ex.example_id,
                dialogue=judge_transcript,
                reference_summary=ex.reference_summary,
                candidate=pred.candidate,
                metrics=metrics_out,
            )
            run.state.records.append(record)
            _maybe_flush_records(run.results_path, run.state.records, flush_every=10)

            score_values = [res.score for res in metrics_out.values()]
            return sum(score_values) / len(score_values) if score_values else 0.0

        return _metric

    def _finalize(self) -> None:
        if self.state.records:
            write_jsonl(self.results_path, (r.model_dump(mode="json", by_alias=True) for r in self.state.records))
            self.state.records.clear()

        metrics_summary = _build_metrics_summary(self.state.metric_scores)
        # split is a HuggingFace concept; a local dataset uses the whole input dir.
        recorded_split = None if self.cfg.dataset.source == "local_dir" else self.split
        summary = _build_run_summary(
            run_id=self.run_id,
            split=recorded_split,
            devset=self.devset,
            metrics_summary=metrics_summary,
            skipped_dimensions=self.skipped_dimensions,
            summarize_ms_values=self.state.summarize_ms_values,
            judge_ms_values=self.state.judge_ms_values,
        )

        self.summary_path.write_bytes(orjson.dumps(summary, option=orjson.OPT_INDENT_2))
        self.hallucination_inputs_path.write_bytes(
            orjson.dumps(
                [h.model_dump() for h in self.state.hallucination_inputs],
                option=orjson.OPT_INDENT_2,
            )
        )

    def run(self) -> tuple[str, Path, Path, Path]:
        self.run_id = str(uuid.uuid4())

        self.results_path, self.summary_path, self.hallucination_inputs_path = prepare_run_paths(
            self.cfg.run.output_dir, self.run_id
        )
        self.devset = load_dspy_devset(self.cfg, self.split, self.limit, self.dataset_path)

        try:
            evaluator = Evaluate(
                devset=self.devset,
                metric=self._build_metric(),
                num_threads=8,
                display_progress=True,
            )
            evaluator(self._build_program())
        finally:
            self._finalize()

        return self.run_id, self.results_path, self.summary_path, self.hallucination_inputs_path


def _maybe_flush_records(results_path: Path, records: list[EvalRecord], *, flush_every: int) -> None:
    if len(records) < flush_every:
        return

    try:
        write_jsonl(results_path, (r.model_dump(mode="json", by_alias=True) for r in records))
        records.clear()
    except OSError:
        logger.exception("Critical I/O error while flushing records to %s", results_path)
        raise


def _collect_rubric_metrics(rubric_evaluation: dict[str, dict]) -> dict[str, MetricResult]:
    """Extract per-dimension rubric scores into MetricResult objects."""
    return {
        f"rubric_{dim}": MetricResult(
            score=int(result["score"]),
            reason=result["rationale"],
        )
        for dim, result in rubric_evaluation["dimensions"].items()
    }


def _build_metrics_summary(metric_scores: dict[str, list[float]]) -> dict[str, dict[str, float]]:
    metrics_summary: dict[str, dict[str, float]] = {
        name: {"mean": float(sum(vals) / len(vals)) if vals else 0.0}
        for name, vals in metric_scores.items()
        if name != "token_usage"
    }
    return metrics_summary


def _build_run_summary(
    *,
    run_id: str,
    split: str | None,
    devset: list[dspy.Example],
    metrics_summary: dict[str, dict[str, float]],
    skipped_dimensions: list[str],
    summarize_ms_values: list[int],
    judge_ms_values: list[int],
) -> RunSummary:
    rubric_scores = [v["mean"] for k, v in metrics_summary.items() if k.startswith("rubric_")]
    overall = float(sum(rubric_scores) / len(rubric_scores)) if rubric_scores else None
    return {
        "run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "split": split,
        "n": len(devset),
        "overall": overall,
        "metrics": metrics_summary,
        # Recorded so a dimension missing from `metrics` reads as deliberately out of scope for this
        # summary path, not as a dimension that silently failed to produce a score.
        "skipped_dimensions": skipped_dimensions,
        "latency_ms": {
            "summarize_p50": _p50(summarize_ms_values),
            "judge_p50": _p50(judge_ms_values),
        },
    }


def run_eval(
    cfg: AppConfig,
    *,
    split: str,
    limit: int | None,
    prompt_version: str,
    dataset_path: Path | None = None,
) -> tuple[str, Path, Path, Path]:
    return EvalRun(
        cfg,
        split=split,
        limit=limit,
        prompt_version=prompt_version,
        dataset_path=dataset_path,
    ).run()
