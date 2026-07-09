from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

import orjson

from evals.summarisation.src.bias.utils import format_dialogue
from evals.summarisation.src.common import AppConfig, MetricResult, call_llm_judge_parallel, write_jsonl
from evals.summarisation.src.security.constants import (
    RESULTS_FILENAME,
    SECURITY_DIMENSIONS_BY_LEVEL,
    SUMMARY_FILENAME,
)
from evals.summarisation.src.security.data.loader import discover_security_files, load_security_json
from evals.summarisation.src.security.security_types import (
    InjectionLevel,
    LevelRollup,
    SecurityEvalRecord,
    SecurityRunSummary,
    SecurityScenarioInput,
)
from evals.summarisation.src.summarizer import generate_summary

logger = logging.getLogger(__name__)


async def evaluate_scenario(
    scenario: SecurityScenarioInput,
    template_name: str | None,
) -> SecurityEvalRecord:
    """Summarise one scenario with the production summariser and score it with the LLM judge."""
    transcript_text = format_dialogue(scenario.dialogue_entries)

    try:
        generated = await generate_summary(scenario.dialogue_entries, template_name)
        summary_text = generated.text
        error: str | None = None
    except Exception as exc:
        logger.exception("Summary generation failed for scenario %s", scenario.scenario_id)
        summary_text = ""
        error = str(exc)

    metrics: dict[str, MetricResult] = {}
    if error is None:
        # Point the right judge at the right level: harmlessness always, plus adherence for
        # benign/borderline or refusal/robustness for malicious.
        dimensions = SECURITY_DIMENSIONS_BY_LEVEL[scenario.injection_level]
        rubric_evaluation = await call_llm_judge_parallel(
            summary_id=scenario.scenario_id,
            transcript_ref=scenario.scenario_id,
            transcript_text=transcript_text,
            summary_text=summary_text,
            dimensions=list(dimensions),
            template_name=template_name,
            intended_solicitation=scenario.intended_solicitation,
        )
        metrics = {
            f"rubric_{dim}": MetricResult(score=int(result["score"]), reason=result["rationale"])
            for dim, result in rubric_evaluation["dimensions"].items()
        }

    return SecurityEvalRecord(
        scenario_id=scenario.scenario_id,
        injection_level=scenario.injection_level,
        intended_solicitation=scenario.intended_solicitation,
        summary_text=summary_text,
        metrics=metrics,
        error=error,
    )


def _dimension_means(records: list[SecurityEvalRecord]) -> dict[str, float]:
    """Mean judge score per dimension, averaged over the records that were scored."""
    scores: dict[str, list[float]] = defaultdict(list)
    for r in records:
        for name, metric in r.metrics.items():
            scores[name].append(metric.score)
    return {name: mean(s) for name, s in scores.items()}


def build_run_summary(run_id: str, records: list[SecurityEvalRecord]) -> SecurityRunSummary:
    """Aggregate per-dimension judge means for each injection level."""
    by_level: dict[str, LevelRollup] = {}
    for level in InjectionLevel:
        level_records = [r for r in records if r.injection_level == level]
        if level_records:
            by_level[level.value] = LevelRollup(n=len(level_records), dimension_means=_dimension_means(level_records))

    return SecurityRunSummary(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        n_scenarios=len(records),
        by_level=by_level,
    )


async def run_security_eval(
    cfg: AppConfig,
    input_dir: Path,
    output_dir: Path,
) -> tuple[str, Path]:
    """Runs the prompt-injection security evaluation over all scenarios in ``input_dir``."""
    run_id = str(uuid.uuid4())
    run_output_dir = output_dir / run_id
    run_output_dir.mkdir(parents=True, exist_ok=True)

    results_path = run_output_dir / RESULTS_FILENAME
    summary_path = run_output_dir / SUMMARY_FILENAME

    template_name = cfg.prompts.summarizer_template_name

    scenario_files = discover_security_files(input_dir)
    logger.info("Found %d injection scenarios to evaluate", len(scenario_files))

    records: list[SecurityEvalRecord] = []
    for file_path in scenario_files:
        scenario = load_security_json(file_path)
        logger.info("Evaluating scenario %s (%s)", scenario.scenario_id, scenario.injection_level)
        record = await evaluate_scenario(scenario, template_name)
        records.append(record)
        # Persist incrementally (write_jsonl appends) so a later failure keeps earlier results.
        write_jsonl(results_path, [record.model_dump(mode="json")])

    summary = build_run_summary(run_id, records)
    summary_path.write_bytes(orjson.dumps(summary.model_dump(), option=orjson.OPT_INDENT_2))

    logger.info("Security evaluation complete. Results written to %s", run_output_dir)
    return run_id, results_path
