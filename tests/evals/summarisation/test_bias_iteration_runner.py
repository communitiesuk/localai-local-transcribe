from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import dspy
import pytest

from common.types import MinuteAndHallucinations
from evals.summarisation.src.bias.bias_types import CounterfactualMetricResult
from evals.summarisation.src.bias.iteration_runner import (
    evaluate_with_judge_detailed,
    run_multiple_iterations,
    run_single_iteration,
)
from evals.summarisation.src.common import DialogExample


@pytest.fixture
def mock_metrics():
    metric1 = MagicMock()
    metric1.name = "faithfulness"
    metric1.evaluate.return_value = MagicMock(score=0.8, reason="Good")

    metric2 = MagicMock()
    metric2.name = "coverage"
    metric2.evaluate.return_value = MagicMock(score=0.7, reason="OK")

    return [metric1, metric2]


@pytest.fixture
def mock_sentiment_analyzer():
    analyzer = MagicMock()
    analyzer.compute_sentiment.return_value = 0.5
    return analyzer


def test_evaluate_with_judge_detailed_single_metric():
    metric = MagicMock()
    metric.name = "faithfulness"
    metric.evaluate.return_value = MagicMock(score=0.9, reason="Excellent")

    example = DialogExample(example_id="1", dialogue="Test", reference_summary=None)
    prediction = dspy.Prediction(summary="Summary", candidate=None)

    results = evaluate_with_judge_detailed([metric], example, prediction)

    assert len(results) == 1
    assert "faithfulness" in results
    assert isinstance(results["faithfulness"], CounterfactualMetricResult)
    assert results["faithfulness"].score == 0.9
    assert results["faithfulness"].reason == "Excellent"
    metric.evaluate.assert_called_once_with(example=example, prediction=prediction)


def test_evaluate_with_judge_detailed_multiple_metrics(mock_metrics):
    example = DialogExample(example_id="1", dialogue="Test", reference_summary=None)
    prediction = dspy.Prediction(summary="Summary", candidate=None)

    results = evaluate_with_judge_detailed(mock_metrics, example, prediction)

    assert len(results) == 2
    assert "faithfulness" in results
    assert "coverage" in results
    assert results["faithfulness"].score == 0.8
    assert results["faithfulness"].reason == "Good"
    assert results["coverage"].score == 0.7
    assert results["coverage"].reason == "OK"
    for metric in mock_metrics:
        metric.evaluate.assert_called_once()


@pytest.mark.asyncio
async def test_run_single_iteration_basic(mock_metrics, mock_sentiment_analyzer):
    from unittest.mock import patch

    dialogue_entries = [{"speaker": "1", "text": "Hello", "start_time": 0.0, "end_time": 1.0}]
    iteration_id = "test_iter_0"

    mock_generate = AsyncMock(
        return_value=MinuteAndHallucinations(text="Generated summary", total_claims=0, hallucinations=[])
    )

    with patch("evals.summarisation.src.bias.iteration_runner.generate_summary", mock_generate):
        summary, metrics, summarize_ms, judge_ms = await run_single_iteration(
            dialogue_entries, iteration_id, mock_metrics, mock_sentiment_analyzer
        )

        assert summary == "Generated summary"
        assert metrics.sentiment_score == 0.5
        assert len(metrics.metrics) == 2
        assert "faithfulness" in metrics.metrics
        assert "coverage" in metrics.metrics
        assert metrics.metrics["faithfulness"].score == 0.8
        assert metrics.metrics["coverage"].score == 0.7
        assert isinstance(summarize_ms, int)
        assert isinstance(judge_ms, int)
        assert summarize_ms >= 0
        assert judge_ms >= 0
        mock_generate.assert_called_once_with(dialogue_entries, None)
        mock_sentiment_analyzer.compute_sentiment.assert_called_once_with("Generated summary")


@pytest.mark.asyncio
async def test_run_single_iteration_with_template(mock_metrics, mock_sentiment_analyzer):
    from unittest.mock import patch

    dialogue_entries = [{"speaker": "1", "text": "Hello", "start_time": 0.0, "end_time": 1.0}]
    iteration_id = "test_iter_0"
    template_name = "custom_template"

    mock_generate = AsyncMock(
        return_value=MinuteAndHallucinations(text="Template summary", total_claims=0, hallucinations=[])
    )

    with patch("evals.summarisation.src.bias.iteration_runner.generate_summary", mock_generate):
        summary, metrics, summarize_ms, judge_ms = await run_single_iteration(
            dialogue_entries, iteration_id, mock_metrics, mock_sentiment_analyzer, template_name=template_name
        )

        assert summary == "Template summary"
        assert metrics.sentiment_score == 0.5
        assert len(metrics.metrics) == 2
        mock_generate.assert_called_once_with(dialogue_entries, template_name)
        mock_sentiment_analyzer.compute_sentiment.assert_called_once_with("Template summary")


@pytest.mark.asyncio
async def test_run_multiple_iterations_basic(mock_metrics, mock_sentiment_analyzer):
    from unittest.mock import patch

    dialogue_entries = [{"speaker": "1", "text": "Hello", "start_time": 0.0, "end_time": 1.0}]
    base_id = "test"
    num_iterations = 3

    mock_generate = AsyncMock(
        return_value=MinuteAndHallucinations(text="Generated summary", total_claims=0, hallucinations=[])
    )

    with patch("evals.summarisation.src.bias.iteration_runner.generate_summary", mock_generate):
        summaries, iterations, total_summarize_ms, total_judge_ms = await run_multiple_iterations(
            dialogue_entries, base_id, num_iterations, mock_metrics, mock_sentiment_analyzer
        )

        assert len(summaries) == num_iterations
        assert len(iterations) == num_iterations
        assert all(s == "Generated summary" for s in summaries)
        assert all(iteration.sentiment_score == 0.5 for iteration in iterations)
        assert all(len(iteration.metrics) == 2 for iteration in iterations)
        assert isinstance(total_summarize_ms, int)
        assert isinstance(total_judge_ms, int)
        assert total_summarize_ms >= 0
        assert total_judge_ms >= 0
        assert mock_generate.call_count == num_iterations
        assert mock_sentiment_analyzer.compute_sentiment.call_count == num_iterations


@pytest.mark.asyncio
async def test_run_multiple_iterations_aggregates_latency(mock_metrics, mock_sentiment_analyzer):
    from unittest.mock import patch

    dialogue_entries = [{"speaker": "1", "text": "Hello", "start_time": 0.0, "end_time": 1.0}]
    base_id = "test"
    num_iterations = 2

    mock_generate = AsyncMock(
        return_value=MinuteAndHallucinations(text="Generated summary", total_claims=0, hallucinations=[])
    )

    with patch("evals.summarisation.src.bias.iteration_runner.generate_summary", mock_generate):
        _summaries, _iterations, total_summarize_ms, total_judge_ms = await run_multiple_iterations(
            dialogue_entries, base_id, num_iterations, mock_metrics, mock_sentiment_analyzer
        )

        assert total_summarize_ms >= 0
        assert total_judge_ms >= 0
        assert isinstance(total_summarize_ms, int)
        assert isinstance(total_judge_ms, int)
