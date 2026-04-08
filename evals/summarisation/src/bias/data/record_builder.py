from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from common.settings import get_settings
from evals.summarisation.src.bias.data.loader import load_counterfactual_json
from evals.summarisation.src.bias.iteration_runner import run_multiple_iterations
from evals.summarisation.src.bias.types import (
    CounterfactualEvalRecord,
    CounterfactualInput,
    IterationMetrics,
    MetricStatistics,
)
from evals.summarisation.src.bias.utils import (
    compute_comparison_statistics,
    compute_metric_statistics,
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


def _build_supplementary_record(
    run_id: str,
    variant_a: CounterfactualEvalRecord,
    variant_b: CounterfactualEvalRecord,
    variant_a_name: str,
    variant_b_name: str,
    sentiment_delta_stats: MetricStatistics,
) -> CounterfactualEvalRecord:
    """Builds supplementary comparison record between two counterfactual variants."""
    return CounterfactualEvalRecord(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        example_id=f"{variant_a.protected_characteristic}_{variant_a_name}_to_{variant_b_name}",
        transcription_text_original=variant_a.transcription_text_counterfactual,
        transcription_text_counterfactual=variant_b.transcription_text_counterfactual,
        hypothesis_summaries_original=variant_a.hypothesis_summaries_counterfactual,
        hypothesis_summaries_counterfactual=variant_b.hypothesis_summaries_counterfactual,
        hypothesis_model=variant_a.hypothesis_model,
        prompt_version=variant_a.prompt_version,
        protected_characteristic=variant_a.protected_characteristic,
        axis_of_change=f"{variant_a_name}_to_{variant_b_name}",
        iterations_original=variant_a.iterations_counterfactual,
        iterations_counterfactual=variant_b.iterations_counterfactual,
        metrics_original_stats=variant_a.metrics_counterfactual_stats,
        metrics_counterfactual_stats=variant_b.metrics_counterfactual_stats,
        sentiment_delta_stats=sentiment_delta_stats,
        latency_ms={"supplementary": 0},
        error=None,
    )


async def generate_supplementary_comparisons(
    baseline_to_variants: dict[str, list[CounterfactualEvalRecord]],
    run_id: str,
    _num_iterations: int,
    _metrics: list,
    _cfg: AppConfig,
) -> list[CounterfactualEvalRecord]:
    """Generates pairwise comparisons between counterfactual variants sharing the same baseline."""
    from evals.summarisation.src.bias.utils import compute_statistics

    supplementary_records = []

    min_variants_for_comparison = 2

    for _baseline_text, variants in baseline_to_variants.items():
        if len(variants) < min_variants_for_comparison:
            continue

        logger.info(
            "Generating %d supplementary comparisons between %d variants sharing the same baseline",
            len(variants) * (len(variants) - 1) // 2,
            len(variants),
        )

        for i in range(len(variants)):
            for j in range(i + 1, len(variants)):
                variant_a = variants[i]
                variant_b = variants[j]

                variant_a_name = variant_a.axis_of_change.split("_to_")[1]
                variant_b_name = variant_b.axis_of_change.split("_to_")[1]

                logger.info(
                    "Creating supplementary comparison: %s vs %s",
                    variant_a_name,
                    variant_b_name,
                )

                sentiment_deltas = [
                    iter_b.sentiment_score - iter_a.sentiment_score
                    for iter_a, iter_b in zip(
                        variant_a.iterations_counterfactual,
                        variant_b.iterations_counterfactual,
                        strict=True,
                    )
                ]

                sentiment_delta_stats = compute_statistics(sentiment_deltas)

                supplementary_record = _build_supplementary_record(
                    run_id, variant_a, variant_b, variant_a_name, variant_b_name, sentiment_delta_stats
                )
                supplementary_records.append(supplementary_record)

    logger.info("Generated %d supplementary comparisons", len(supplementary_records))
    return supplementary_records
