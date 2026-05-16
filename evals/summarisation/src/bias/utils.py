from __future__ import annotations

import statistics

from common.database.postgres_models import DialogueEntry
from evals.summarisation.src.bias.bias_types import IterationMetrics, MetricStatistics


def format_dialogue(dialogue_entries: list[DialogueEntry]) -> str:
    """
    Formats dialogue entries into a readable text representation.
    """
    lines = []
    for entry in dialogue_entries:
        speaker = entry["speaker"]
        text = entry["text"]
        lines.append(f"Speaker {speaker}: {text}")
    return "\n".join(lines)


def parse_group_names(axis_of_change: str) -> tuple[str, str]:
    """
    Parses axis of change string into formatted group names.
    """
    parts = axis_of_change.split("_to_")
    expected_parts = 2
    if len(parts) != expected_parts:
        msg = f"Invalid axis_of_change format: {axis_of_change}. Expected 'value1_to_value2'"
        raise ValueError(msg)
    return (parts[0].replace("_", " ").title(), parts[1].replace("_", " ").title())


def compute_statistics(values: list[float]) -> MetricStatistics:
    """
    Computes mean, standard deviation, and stores values for a list of floats.
    """
    if not values:
        msg = "Cannot compute statistics on empty list"
        raise ValueError(msg)
    return MetricStatistics(
        mean=statistics.mean(values),
        std=statistics.stdev(values) if len(values) > 1 else 0.0,
        values=values,
    )


def compute_metric_statistics(
    iterations: list[IterationMetrics],
) -> dict[str, MetricStatistics]:
    """
    Computes statistics for each metric across multiple iterations.
    """
    if not iterations:
        msg = "Cannot compute metric statistics on empty iterations list"
        raise ValueError(msg)
    stats = {}
    for metric_name in iterations[0].metrics:
        scores = [iteration.metrics[metric_name].score for iteration in iterations]
        stats[metric_name] = compute_statistics(scores)
    return stats


def compute_comparison_statistics(
    original_iterations: list[IterationMetrics],
    cf_iterations: list[IterationMetrics],
) -> MetricStatistics:
    """
    Computes statistics for sentiment score differences between original and counterfactual iterations.
    """
    sentiment_deltas = [
        cf_iter.sentiment_score - orig_iter.sentiment_score
        for orig_iter, cf_iter in zip(original_iterations, cf_iterations, strict=True)
    ]
    return compute_statistics(sentiment_deltas)


def compute_regard_comparison_statistics(
    original_iterations: list[IterationMetrics],
    cf_iterations: list[IterationMetrics],
) -> MetricStatistics | None:
    """
    Computes statistics for REGARD negative score differences between original and counterfactual iterations.
    """
    if not all(iteration.regard_scores for iteration in original_iterations + cf_iterations):
        return None

    # delta_negative = counterfactual.negative - factual.negative
    # Positive values indicate the counterfactual text attracted more negative sentiment.
    regard_deltas = [
        cf_iter.regard_scores["negative"] - orig_iter.regard_scores["negative"]
        for orig_iter, cf_iter in zip(original_iterations, cf_iterations, strict=True)
        if orig_iter.regard_scores and cf_iter.regard_scores
    ]

    if not regard_deltas:
        return None

    return compute_statistics(regard_deltas)
