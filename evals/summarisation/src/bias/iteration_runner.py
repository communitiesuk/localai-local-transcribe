from __future__ import annotations

import logging
import time
from typing import Any

import dspy

from common.database.postgres_models import DialogueEntry
from evals.summarisation.src.bias.bias_types import CounterfactualMetricResult, IterationMetrics
from evals.summarisation.src.bias.sentiment_analyzer import sentiment_score_from_distribution
from evals.summarisation.src.common import DialogExample, judge_transcript_text
from evals.summarisation.src.summarizer import generate_summary

logger = logging.getLogger(__name__)


async def evaluate_with_judge_detailed(
    metrics: list, example: DialogExample, prediction: dspy.Prediction
) -> dict[str, CounterfactualMetricResult]:
    """
    Evaluates prediction using multiple judge metrics and returns detailed results.
    """
    results = {}
    for metric in metrics:
        result = await metric.evaluate_async(example=example, prediction=prediction)
        results[metric.name] = CounterfactualMetricResult(score=result.score, reason=result.reason)
    return results


async def run_single_iteration(
    dialogue_entries: list[DialogueEntry],
    iteration_id: str,
    metrics: list[Any],
    sentiment_analyzer: Any,
    regard_scorer: Any = None,
    template_name: str | None = None,
) -> tuple[str, IterationMetrics, int, int]:
    """
    Runs a single iteration of summary generation, evaluation, and sentiment analysis.
    """
    t0 = time.perf_counter()
    generated = await generate_summary(dialogue_entries, template_name)
    summary = generated.text
    t1 = time.perf_counter()
    summarize_ms = int((t1 - t0) * 1000)

    example = DialogExample(
        example_id=iteration_id,
        dialogue=judge_transcript_text(dialogue_entries),
        reference_summary=None,
    )
    pred = dspy.Prediction(summary=summary, candidate=None)

    t0_judge = time.perf_counter()
    judge_results = await evaluate_with_judge_detailed(metrics, example, pred)
    t1_judge = time.perf_counter()
    judge_ms = int((t1_judge - t0_judge) * 1000)

    sentiment_distribution = sentiment_analyzer.compute_sentiment_distribution(summary)
    sentiment_score = sentiment_score_from_distribution(sentiment_distribution)
    regard_scores = None
    if regard_scorer:
        regard_result = regard_scorer.score_summary(summary)
        regard_scores = regard_result.distribution.as_dict()

    logger.debug(
        "Sentiment for iteration %s: score=%.4f, summary_preview=%s",
        iteration_id,
        sentiment_score,
        summary[:100] if summary else "EMPTY",
    )

    iteration_metrics = IterationMetrics(
        metrics=judge_results,
        sentiment_score=sentiment_score,
        sentiment_distribution=sentiment_distribution,
        regard_scores=regard_scores,
    )

    return summary, iteration_metrics, summarize_ms, judge_ms


async def run_multiple_iterations(
    dialogue_entries: list[DialogueEntry],
    base_id: str,
    num_iterations: int,
    metrics: list[Any],
    sentiment_analyzer: Any,
    regard_scorer: Any = None,
    template_name: str | None = None,
) -> tuple[list[str], list[IterationMetrics], int, int]:
    """
    Runs multiple iterations of summary generation and aggregates results.
    """
    summaries = []
    iterations = []
    total_summarize_ms = 0
    total_judge_ms = 0

    for iteration in range(num_iterations):
        iteration_id = f"{base_id}_iter_{iteration}"
        summary, iteration_metrics, summarize_ms, judge_ms = await run_single_iteration(
            dialogue_entries, iteration_id, metrics, sentiment_analyzer, regard_scorer, template_name
        )
        summaries.append(summary)
        iterations.append(iteration_metrics)
        total_summarize_ms += summarize_ms
        total_judge_ms += judge_ms

    return summaries, iterations, total_summarize_ms, total_judge_ms
