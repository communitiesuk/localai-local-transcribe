from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from common.settings import get_settings
from evals.summarisation.src.bias.bias_types import (
    CounterfactualEvalRecord,
    CounterfactualInput,
    IterationMetrics,
)
from evals.summarisation.src.bias.data.loader import load_counterfactual_json
from evals.summarisation.src.bias.iteration_runner import run_multiple_iterations
from evals.summarisation.src.bias.utils import (
    compute_comparison_statistics,
    compute_metric_statistics,
    compute_regard_comparison_statistics,
    format_dialogue,
)
from evals.summarisation.src.common import AppConfig

logger = logging.getLogger(__name__)
settings = get_settings()


def build_counterfactual_record(
    run_id: str,
    counterfactual_input: CounterfactualInput,
    original_summaries: list[str],
    original_iterations: list[IterationMetrics],
    cf_summaries: list[str],
    cf_iterations: list[IterationMetrics],
    total_summarize_ms_orig: int,
    total_judge_ms_orig: int,
    total_summarize_ms_cf: int,
    total_judge_ms_cf: int,
    cfg: AppConfig,
) -> CounterfactualEvalRecord:
    """Builds complete evaluation record from original and counterfactual iteration results."""
    metrics_original_stats = compute_metric_statistics(original_iterations)
    metrics_cf_stats = compute_metric_statistics(cf_iterations)
    sentiment_delta_stats = compute_comparison_statistics(original_iterations, cf_iterations)
    regard_delta_stats = compute_regard_comparison_statistics(original_iterations, cf_iterations)

    return CounterfactualEvalRecord(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        example_id=counterfactual_input.variant_id,
        transcription_text_original=format_dialogue(counterfactual_input.original_dialogue_entries),
        transcription_text_counterfactual=format_dialogue(counterfactual_input.counterfactual_dialogue_entries),
        hypothesis_summaries_original=original_summaries,
        hypothesis_summaries_counterfactual=cf_summaries,
        hypothesis_model=settings.BEST_LLM_MODEL_NAME,
        prompt_version=cfg.run.prompt_version,
        protected_characteristic=counterfactual_input.protected_characteristic,
        axis_of_change=counterfactual_input.axis_of_change,
        iterations_original=original_iterations,
        iterations_counterfactual=cf_iterations,
        metrics_original_stats=metrics_original_stats,
        metrics_counterfactual_stats=metrics_cf_stats,
        sentiment_delta_stats=sentiment_delta_stats,
        regard_delta_stats=regard_delta_stats,
        latency_ms={
            "summarize_original": total_summarize_ms_orig,
            "judge_original": total_judge_ms_orig,
            "summarize_counterfactual": total_summarize_ms_cf,
            "judge_counterfactual": total_judge_ms_cf,
        },
        error=None,
    )


async def process_counterfactual_file(
    file_path: Path,
    run_id: str,
    num_iterations: int,
    metrics: list[Any],
    sentiment_analyzer: Any,
    regard_scorer: Any,
    cfg: AppConfig,
    baseline_cache: dict[str, tuple[list[str], list[IterationMetrics], int, int]],
    template_name: str | None = None,
) -> CounterfactualEvalRecord:
    """Processes counterfactual file by generating summaries for original and counterfactual transcripts."""
    logger.info("Processing file: %s", file_path.name)
    counterfactual_input = load_counterfactual_json(file_path)

    baseline_text = format_dialogue(counterfactual_input.original_dialogue_entries)

    if baseline_text in baseline_cache:
        logger.info("Using cached baseline results for: %s", file_path.name)
        (
            original_summaries,
            original_iterations,
            total_summarize_ms_orig,
            total_judge_ms_orig,
        ) = baseline_cache[baseline_text]
    else:
        logger.info("Generating %d original summaries...", num_iterations)
        (
            original_summaries,
            original_iterations,
            total_summarize_ms_orig,
            total_judge_ms_orig,
        ) = await run_multiple_iterations(
            counterfactual_input.original_dialogue_entries,
            "original",
            num_iterations,
            metrics,
            sentiment_analyzer,
            regard_scorer,
            template_name,
        )
        baseline_cache[baseline_text] = (
            original_summaries,
            original_iterations,
            total_summarize_ms_orig,
            total_judge_ms_orig,
        )

    logger.info(
        "Processing counterfactual: %s (%s -> %s)",
        counterfactual_input.variant_id,
        counterfactual_input.protected_characteristic,
        counterfactual_input.axis_of_change,
    )

    logger.info("Generating %d counterfactual summaries...", num_iterations)
    cf_summaries, cf_iterations, total_summarize_ms_cf, total_judge_ms_cf = await run_multiple_iterations(
        counterfactual_input.counterfactual_dialogue_entries,
        counterfactual_input.variant_id,
        num_iterations,
        metrics,
        sentiment_analyzer,
        regard_scorer,
        template_name,
    )

    return build_counterfactual_record(
        run_id,
        counterfactual_input,
        original_summaries,
        original_iterations,
        cf_summaries,
        cf_iterations,
        total_summarize_ms_orig,
        total_judge_ms_orig,
        total_summarize_ms_cf,
        total_judge_ms_cf,
        cfg,
    )
