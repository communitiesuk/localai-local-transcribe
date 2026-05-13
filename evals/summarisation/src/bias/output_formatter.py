from __future__ import annotations

import statistics
from datetime import UTC, datetime

from common.settings import get_settings
from evals.summarisation.src.bias.bias_types import (
    AggregatedResultsMap,
    CharacteristicAxisMap,
    ComparisonMetrics,
    CounterfactualEvalRecord,
    CounterfactualRunSummary,
    PlottingOutput,
    PlottingRecord,
)
from evals.summarisation.src.bias.regard_scorer import REGARDScorer
from evals.summarisation.src.bias.sentiment_analyzer import SentimentAnalyzer
from evals.summarisation.src.bias.utils import parse_group_names
from evals.summarisation.src.common import AppConfig

settings = get_settings()


def create_plotting_output(
    records: list[CounterfactualEvalRecord],
    supplementary_records: list[CounterfactualEvalRecord],
    run_id: str,
    cfg: AppConfig,
    num_iterations: int,
) -> PlottingOutput:
    """
    Creates plotting output from evaluation records for visualization.
    """
    plotting_records = []

    for idx, record in enumerate(records):
        group_a_name, group_b_name = parse_group_names(record.axis_of_change)

        comparison_metrics = []
        for metric_name in record.metrics_original_stats:
            orig_stats = record.metrics_original_stats[metric_name]
            cf_stats = record.metrics_counterfactual_stats[metric_name]

            comparison_metrics.append(
                ComparisonMetrics(
                    metric_name=metric_name,
                    original_mean=orig_stats.mean,
                    original_std=orig_stats.std,
                    counterfactual_mean=cf_stats.mean,
                    counterfactual_std=cf_stats.std,
                    delta=cf_stats.mean - orig_stats.mean,
                    original_values=orig_stats.values,
                    counterfactual_values=cf_stats.values,
                )
            )

        orig_sentiment_values = [iter_orig.sentiment_score for iter_orig in record.iterations_original]
        cf_sentiment_values = [iter_cf.sentiment_score for iter_cf in record.iterations_counterfactual]

        comparison_metrics.append(
            ComparisonMetrics(
                metric_name="sentiment",
                original_mean=statistics.mean(orig_sentiment_values),
                original_std=statistics.stdev(orig_sentiment_values) if len(orig_sentiment_values) > 1 else 0.0,
                counterfactual_mean=statistics.mean(cf_sentiment_values),
                counterfactual_std=statistics.stdev(cf_sentiment_values) if len(cf_sentiment_values) > 1 else 0.0,
                delta=statistics.mean(cf_sentiment_values) - statistics.mean(orig_sentiment_values),
                original_values=orig_sentiment_values,
                counterfactual_values=cf_sentiment_values,
            )
        )

        orig_regard_values = [
            iter_orig.regard_scores["negative"] for iter_orig in record.iterations_original if iter_orig.regard_scores
        ]
        cf_regard_values = [
            iter_cf.regard_scores["negative"] for iter_cf in record.iterations_counterfactual if iter_cf.regard_scores
        ]

        if orig_regard_values and cf_regard_values:
            comparison_metrics.append(
                ComparisonMetrics(
                    metric_name="regard (negative)",
                    original_mean=statistics.mean(orig_regard_values),
                    original_std=statistics.stdev(orig_regard_values) if len(orig_regard_values) > 1 else 0.0,
                    counterfactual_mean=statistics.mean(cf_regard_values),
                    counterfactual_std=statistics.stdev(cf_regard_values) if len(cf_regard_values) > 1 else 0.0,
                    delta=statistics.mean(cf_regard_values) - statistics.mean(orig_regard_values),
                    original_values=orig_regard_values,
                    counterfactual_values=cf_regard_values,
                )
            )

        plotting_records.append(
            PlottingRecord(
                comparison_id=f"{record.protected_characteristic}_{record.axis_of_change}_{idx}",
                protected_characteristic=record.protected_characteristic,
                axis_of_change=record.axis_of_change,
                group_a_name=group_a_name,
                group_b_name=group_b_name,
                is_supplementary=False,
                metrics=comparison_metrics,
                sentiment_delta=record.sentiment_delta_stats,
                regard_delta=record.regard_delta_stats,
                num_iterations=num_iterations,
                hypothesis_model=record.hypothesis_model,
                prompt_version=record.prompt_version,
            )
        )

    sentiment_analyzer = SentimentAnalyzer()
    regard_scorer = REGARDScorer()

    for idx, record in enumerate(supplementary_records):
        group_a_name, group_b_name = parse_group_names(record.axis_of_change)

        comparison_metrics = []
        for metric_name in record.metrics_original_stats:
            orig_stats = record.metrics_original_stats[metric_name]
            cf_stats = record.metrics_counterfactual_stats[metric_name]

            comparison_metrics.append(
                ComparisonMetrics(
                    metric_name=metric_name,
                    original_mean=orig_stats.mean,
                    original_std=orig_stats.std,
                    counterfactual_mean=cf_stats.mean,
                    counterfactual_std=cf_stats.std,
                    delta=cf_stats.mean - orig_stats.mean,
                    original_values=orig_stats.values,
                    counterfactual_values=cf_stats.values,
                )
            )

        orig_sentiment_values = [
            sentiment_analyzer.compute_sentiment(summary) for summary in record.hypothesis_summaries_original
        ]
        cf_sentiment_values = [
            sentiment_analyzer.compute_sentiment(summary) for summary in record.hypothesis_summaries_counterfactual
        ]

        comparison_metrics.append(
            ComparisonMetrics(
                metric_name="sentiment",
                original_mean=statistics.mean(orig_sentiment_values),
                original_std=statistics.stdev(orig_sentiment_values) if len(orig_sentiment_values) > 1 else 0.0,
                counterfactual_mean=statistics.mean(cf_sentiment_values),
                counterfactual_std=statistics.stdev(cf_sentiment_values) if len(cf_sentiment_values) > 1 else 0.0,
                delta=statistics.mean(cf_sentiment_values) - statistics.mean(orig_sentiment_values),
                original_values=orig_sentiment_values,
                counterfactual_values=cf_sentiment_values,
            )
        )

        orig_regard_values = [
            regard_scorer.score_summary(summary).negative for summary in record.hypothesis_summaries_original
        ]
        cf_regard_values = [
            regard_scorer.score_summary(summary).negative for summary in record.hypothesis_summaries_counterfactual
        ]

        comparison_metrics.append(
            ComparisonMetrics(
                metric_name="regard (negative)",
                original_mean=statistics.mean(orig_regard_values),
                original_std=statistics.stdev(orig_regard_values) if len(orig_regard_values) > 1 else 0.0,
                counterfactual_mean=statistics.mean(cf_regard_values),
                counterfactual_std=statistics.stdev(cf_regard_values) if len(cf_regard_values) > 1 else 0.0,
                delta=statistics.mean(cf_regard_values) - statistics.mean(orig_regard_values),
                original_values=orig_regard_values,
                counterfactual_values=cf_regard_values,
            )
        )

        plotting_records.append(
            PlottingRecord(
                comparison_id=f"{record.protected_characteristic}_{record.axis_of_change}_supplementary_{idx}",
                protected_characteristic=record.protected_characteristic,
                axis_of_change=record.axis_of_change,
                group_a_name=group_a_name,
                group_b_name=group_b_name,
                is_supplementary=True,
                metrics=comparison_metrics,
                sentiment_delta=record.sentiment_delta_stats,
                regard_delta=record.regard_delta_stats,
                num_iterations=num_iterations,
                hypothesis_model=record.hypothesis_model,
                prompt_version=record.prompt_version,
            )
        )

    return PlottingOutput(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        dataset_version=cfg.run.dataset_version,
        engine_version=settings.BEST_LLM_MODEL_NAME,
        prompt_version=cfg.run.prompt_version,
        num_iterations=num_iterations,
        comparisons=plotting_records,
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
