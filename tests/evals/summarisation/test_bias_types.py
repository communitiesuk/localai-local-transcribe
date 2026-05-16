from __future__ import annotations

import pytest
from pydantic import ValidationError

from evals.summarisation.src.bias.bias_types import (
    AxisChange,
    CounterfactualEvalRecord,
    CounterfactualInput,
    CounterfactualMetricResult,
    IterationMetrics,
    MetricStatistics,
    OriginalTranscript,
)


def test_counterfactual_metric_result_valid():
    result = CounterfactualMetricResult(score=0.8, reason="Good quality")
    assert result.score == 0.8
    assert result.reason == "Good quality"


def test_counterfactual_metric_result_score_bounds():
    with pytest.raises(ValidationError):
        CounterfactualMetricResult(score=1.5, reason="Invalid")

    with pytest.raises(ValidationError):
        CounterfactualMetricResult(score=-0.5, reason="Invalid")


def test_iteration_metrics_valid():
    metrics = IterationMetrics(
        metrics={
            "faithfulness": CounterfactualMetricResult(score=0.8, reason="Good"),
            "coverage": CounterfactualMetricResult(score=0.7, reason="OK"),
        },
        sentiment_score=0.5,
    )
    assert len(metrics.metrics) == 2
    assert metrics.sentiment_score == 0.5


def test_iteration_metrics_sentiment_bounds():
    with pytest.raises(ValidationError):
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
            sentiment_score=1.5,
        )

    with pytest.raises(ValidationError):
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
            sentiment_score=-1.5,
        )


def test_metric_statistics_valid():
    stats = MetricStatistics(mean=0.75, std=0.05, values=[0.7, 0.8])
    assert stats.mean == 0.75
    assert stats.std == 0.05
    assert len(stats.values) == 2


def test_axis_change_valid():
    axis_change = AxisChange(
        axis="gender",
        original_value="male",
        target_value="female",
        instructions="Change male to female",
    )
    assert axis_change.axis == "gender"
    assert axis_change.original_value == "male"
    assert axis_change.target_value == "female"


def test_original_transcript_valid():
    transcript = OriginalTranscript(
        dialogue_entries=[{"speaker": "1", "text": "Hello", "start_time": 0.0, "end_time": 1.0}],
        metadata={"source": "test"},
    )
    assert len(transcript.dialogue_entries) == 1
    assert transcript.metadata["source"] == "test"


def test_counterfactual_input_properties():
    cf_input = CounterfactualInput(
        original_transcript=OriginalTranscript(
            dialogue_entries=[{"speaker": "1", "text": "Hello", "start_time": 0.0, "end_time": 1.0}],
            metadata={},
        ),
        rewritten_transcript=[{"speaker": "1", "text": "Hi", "start_time": 0.0, "end_time": 1.0}],
        axis_change=AxisChange(
            axis="gender",
            original_value="male",
            target_value="female",
            instructions="Change",
        ),
        model_version="gpt-4",
        prompt_version="v1",
        evidence_spans_modified=[0],
    )

    assert cf_input.protected_characteristic == "gender"
    assert cf_input.axis_of_change == "male_to_female"
    assert cf_input.variant_id == "gender_male_to_female"
    assert len(cf_input.original_dialogue_entries) == 1
    assert len(cf_input.counterfactual_dialogue_entries) == 1


def test_counterfactual_eval_record_valid():
    record = CounterfactualEvalRecord(
        run_id="test-run",
        timestamp="2024-01-01T00:00:00Z",
        example_id="test_example",
        transcription_text_original="Original text",
        transcription_text_counterfactual="Counterfactual text",
        hypothesis_summaries_original=["Summary 1"],
        hypothesis_summaries_counterfactual=["Summary 2"],
        hypothesis_model="gpt-4",
        prompt_version="v1",
        protected_characteristic="gender",
        axis_of_change="male_to_female",
        iterations_original=[
            IterationMetrics(
                metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
                sentiment_score=0.5,
            )
        ],
        iterations_counterfactual=[
            IterationMetrics(
                metrics={"faithfulness": CounterfactualMetricResult(score=0.7, reason="OK")},
                sentiment_score=0.4,
            )
        ],
        metrics_original_stats={"faithfulness": MetricStatistics(mean=0.8, std=0.0, values=[0.8])},
        metrics_counterfactual_stats={"faithfulness": MetricStatistics(mean=0.7, std=0.0, values=[0.7])},
        sentiment_delta_stats=MetricStatistics(mean=-0.1, std=0.0, values=[-0.1]),
        latency_ms={"summarize_original": 100},
    )

    assert record.run_id == "test-run"
    assert record.protected_characteristic == "gender"
    assert record.error is None


def test_counterfactual_eval_record_with_error():
    record = CounterfactualEvalRecord(
        run_id="test-run",
        timestamp="2024-01-01T00:00:00Z",
        example_id="test_example",
        transcription_text_original="Original text",
        transcription_text_counterfactual="Counterfactual text",
        hypothesis_summaries_original=["Summary 1"],
        hypothesis_summaries_counterfactual=["Summary 2"],
        hypothesis_model="gpt-4",
        prompt_version="v1",
        protected_characteristic="gender",
        axis_of_change="male_to_female",
        iterations_original=[
            IterationMetrics(
                metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
                sentiment_score=0.5,
            )
        ],
        iterations_counterfactual=[
            IterationMetrics(
                metrics={"faithfulness": CounterfactualMetricResult(score=0.7, reason="OK")},
                sentiment_score=0.4,
            )
        ],
        metrics_original_stats={"faithfulness": MetricStatistics(mean=0.8, std=0.0, values=[0.8])},
        metrics_counterfactual_stats={"faithfulness": MetricStatistics(mean=0.7, std=0.0, values=[0.7])},
        sentiment_delta_stats=MetricStatistics(mean=-0.1, std=0.0, values=[-0.1]),
        latency_ms={"summarize_original": 100},
        error={"type": "ValueError", "message": "Test error"},
    )

    assert record.error is not None
    assert record.error["type"] == "ValueError"
