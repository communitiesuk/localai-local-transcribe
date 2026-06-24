from __future__ import annotations

import logging
import statistics
from datetime import UTC, datetime

from common.settings import get_settings
from evals.summarisation.src.bias.bias_types import (
    AggregatedResultsMap,
    BiasEvalResults,
    CharacteristicAxisMap,
    ComparisonMetrics,
    ComparisonResult,
    CounterfactualEvalRecord,
    CounterfactualRunSummary,
    IterationMetrics,
)
from evals.summarisation.src.bias.regard_scorer import REGARDScorer
from evals.summarisation.src.bias.sentiment_analyzer import SentimentAnalyzer
from evals.summarisation.src.bias.utils import parse_group_names
from evals.summarisation.src.common import AppConfig

settings = get_settings()

logger = logging.getLogger(__name__)


def _collect_sentiment_distributions(iterations: list[IterationMetrics]) -> list[dict[str, float]]:
    """Gather the per-iteration raw sentiment distributions (debug signal); empty if absent."""
    return [it.sentiment_distribution for it in iterations if it.sentiment_distribution is not None]


def _stats_metric(name: str, original: list[float], counterfactual: list[float]) -> ComparisonMetrics:
    """Builds a comparison metric from raw original/counterfactual value lists."""
    return ComparisonMetrics(
        metric_name=name,
        original_mean=statistics.mean(original),
        original_std=statistics.stdev(original) if len(original) > 1 else 0.0,
        counterfactual_mean=statistics.mean(counterfactual),
        counterfactual_std=statistics.stdev(counterfactual) if len(counterfactual) > 1 else 0.0,
        delta=statistics.mean(counterfactual) - statistics.mean(original),
        original_values=original,
        counterfactual_values=counterfactual,
    )


def _comparison_metrics(
    record: CounterfactualEvalRecord,
    orig_sentiment: list[float],
    cf_sentiment: list[float],
    orig_regard: list[float],
    cf_regard: list[float],
) -> list[ComparisonMetrics]:
    """Assembles judge, sentiment and (when present) regard metrics for one comparison."""
    metrics = [
        _stats_metric(
            name,
            record.metrics_original_stats[name].values,
            record.metrics_counterfactual_stats[name].values,
        )
        for name in record.metrics_original_stats
    ]
    metrics.append(_stats_metric("sentiment", orig_sentiment, cf_sentiment))
    if orig_regard and cf_regard:
        metrics.append(_stats_metric("regard (negative)", orig_regard, cf_regard))
    return metrics


def _comparison_result(
    record: CounterfactualEvalRecord,
    comparison_id: str,
    metrics: list[ComparisonMetrics],
    num_iterations: int,
    *,
    is_supplementary: bool,
) -> ComparisonResult:
    """Wraps a record's metrics into a serialisable comparison result."""
    group_a_name, group_b_name = parse_group_names(record.axis_of_change)
    return ComparisonResult(
        comparison_id=comparison_id,
        protected_characteristic=record.protected_characteristic,
        axis_of_change=record.axis_of_change,
        group_a_name=group_a_name,
        group_b_name=group_b_name,
        is_supplementary=is_supplementary,
        metrics=metrics,
        sentiment_delta=record.sentiment_delta_stats,
        regard_delta=record.regard_delta_stats,
        sentiment_distribution_original=_collect_sentiment_distributions(record.iterations_original),
        sentiment_distribution_counterfactual=_collect_sentiment_distributions(record.iterations_counterfactual),
        num_iterations=num_iterations,
        hypothesis_model=record.hypothesis_model,
        prompt_version=record.prompt_version,
    )


def build_results(
    records: list[CounterfactualEvalRecord],
    supplementary_records: list[CounterfactualEvalRecord],
    run_id: str,
    cfg: AppConfig,
    num_iterations: int,
) -> BiasEvalResults:
    """
    Builds the per-comparison output from evaluation records.

    Threshold verdicts (SPC and 4/5) are attached afterwards by
    ``thresholds.apply_thresholds``; this function is concerned only with the
    per-comparison metrics.
    """
    comparison_results = []

    for idx, record in enumerate(records):
        metrics = _comparison_metrics(
            record,
            [it.sentiment_score for it in record.iterations_original],
            [it.sentiment_score for it in record.iterations_counterfactual],
            [it.regard_scores["negative"] for it in record.iterations_original if it.regard_scores],
            [it.regard_scores["negative"] for it in record.iterations_counterfactual if it.regard_scores],
        )
        comparison_id = f"{record.protected_characteristic}_{record.axis_of_change}_{idx}"
        comparison_results.append(
            _comparison_result(record, comparison_id, metrics, num_iterations, is_supplementary=False)
        )

    sentiment_analyzer = SentimentAnalyzer()
    regard_scorer = REGARDScorer()

    for idx, record in enumerate(supplementary_records):
        metrics = _comparison_metrics(
            record,
            [sentiment_analyzer.compute_sentiment(s) for s in record.hypothesis_summaries_original],
            [sentiment_analyzer.compute_sentiment(s) for s in record.hypothesis_summaries_counterfactual],
            [regard_scorer.score_summary(s).negative for s in record.hypothesis_summaries_original],
            [regard_scorer.score_summary(s).negative for s in record.hypothesis_summaries_counterfactual],
        )
        comparison_id = f"{record.protected_characteristic}_{record.axis_of_change}_supplementary_{idx}"
        comparison_results.append(
            _comparison_result(record, comparison_id, metrics, num_iterations, is_supplementary=True)
        )

    return BiasEvalResults(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        dataset_version=cfg.run.dataset_version,
        engine_version=settings.BEST_LLM_MODEL_NAME,
        prompt_version=cfg.run.prompt_version,
        num_iterations=num_iterations,
        comparisons=comparison_results,
    )


def create_summary(records: list[CounterfactualEvalRecord], run_id: str, cfg: AppConfig) -> CounterfactualRunSummary:
    """
    Creates aggregated summary from evaluation records grouped by characteristic and axis.
    """
    by_characteristic: CharacteristicAxisMap = {}

    for record in records:
        characteristic = record.protected_characteristic
        axis_of_change = record.axis_of_change

        if characteristic not in by_characteristic:
            by_characteristic[characteristic] = {}
        if axis_of_change not in by_characteristic[characteristic]:
            by_characteristic[characteristic][axis_of_change] = []

        by_characteristic[characteristic][axis_of_change].append(record)

    aggregated: AggregatedResultsMap = {}
    for characteristic, axes_map in by_characteristic.items():
        aggregated[characteristic] = {}
        for axis_of_change, records_list in axes_map.items():
            num_records = len(records_list)

            avg_sentiment_delta_mean = sum(r.sentiment_delta_stats.mean for r in records_list) / num_records
            regard_deltas = [r.regard_delta_stats.mean for r in records_list if r.regard_delta_stats]
            avg_regard_delta_mean = sum(regard_deltas) / len(regard_deltas) if regard_deltas else None

            judge_deltas_mean: dict[str, list[float]] = {}
            for record in records_list:
                for metric_name in record.metrics_original_stats:
                    if metric_name not in judge_deltas_mean:
                        judge_deltas_mean[metric_name] = []
                    delta = (
                        record.metrics_counterfactual_stats[metric_name].mean
                        - record.metrics_original_stats[metric_name].mean
                    )
                    judge_deltas_mean[metric_name].append(delta)

            avg_judge_deltas = {
                metric_name: sum(delta_values) / len(delta_values)
                for metric_name, delta_values in judge_deltas_mean.items()
            }

            aggregated[characteristic][axis_of_change] = {
                "num_comparisons": num_records,
                "avg_sentiment_delta": avg_sentiment_delta_mean,
                "avg_regard_delta": avg_regard_delta_mean,
                "avg_judge_score_delta": avg_judge_deltas,
            }

    return CounterfactualRunSummary(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        dataset_version=cfg.run.dataset_version,
        engine_version=settings.BEST_LLM_MODEL_NAME,
        prompt_version=cfg.run.prompt_version,
        n_comparisons=len(records),
        by_characteristic_and_axis=aggregated,
    )
