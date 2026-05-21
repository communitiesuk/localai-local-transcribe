from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from evals.summarisation.src.bias.bias_types import (
    CounterfactualEvalRecord,
    CounterfactualMetricResult,
    IterationMetrics,
    MetricStatistics,
)
from evals.summarisation.src.bias.output_formatter import create_plotting_output, create_summary
from evals.summarisation.src.common import AppConfig


@pytest.fixture
def sample_config():
    return AppConfig.model_validate(
        {
            "run": {
                "output_dir": "test_output",
                "dataset_version": "v1.0",
                "prompt_version": "v1",
            },
            "dataset": {"name": "test_dataset"},
            "judge": {"pass_threshold": 4},
            "prompts": {
                "summarizer_template_path": "prompts/summarizer.jinja2",
                "judge_template_path": "prompts/judge.jinja2",
            },
        }
    )


@pytest.fixture
def sample_iteration_metrics():
    return [
        IterationMetrics(
            metrics={
                "faithfulness": CounterfactualMetricResult(score=0.8, reason="Good"),
                "coverage": CounterfactualMetricResult(score=0.7, reason="OK"),
            },
            sentiment_score=0.5,
        ),
        IterationMetrics(
            metrics={
                "faithfulness": CounterfactualMetricResult(score=0.9, reason="Great"),
                "coverage": CounterfactualMetricResult(score=0.8, reason="Better"),
            },
            sentiment_score=0.6,
        ),
    ]


@pytest.fixture
def sample_record(sample_iteration_metrics):
    return CounterfactualEvalRecord(
        run_id="test-run-123",
        timestamp=datetime.now(UTC).isoformat(),
        example_id="gender_male_to_female",
        transcription_text_original="Speaker 1: Hello",
        transcription_text_counterfactual="Speaker 1: Hi",
        hypothesis_summaries_original=["Summary 1", "Summary 2"],
        hypothesis_summaries_counterfactual=["Summary A", "Summary B"],
        hypothesis_model="test-model",
        prompt_version="v1",
        protected_characteristic="gender",
        axis_of_change="male_to_female",
        iterations_original=sample_iteration_metrics,
        iterations_counterfactual=sample_iteration_metrics,
        metrics_original_stats={
            "faithfulness": MetricStatistics(mean=0.85, std=0.05, values=[0.8, 0.9]),
            "coverage": MetricStatistics(mean=0.75, std=0.05, values=[0.7, 0.8]),
        },
        metrics_counterfactual_stats={
            "faithfulness": MetricStatistics(mean=0.80, std=0.05, values=[0.75, 0.85]),
            "coverage": MetricStatistics(mean=0.70, std=0.05, values=[0.65, 0.75]),
        },
        sentiment_delta_stats=MetricStatistics(mean=0.05, std=0.02, values=[0.05, 0.05]),
        latency_ms={"summarize_original": 100, "judge_original": 50},
    )


def test_create_summary_single_record(sample_config, sample_record):
    records = [sample_record]
    run_id = "test-run-123"

    summary = create_summary(records, run_id, sample_config)

    assert summary.run_id == run_id
    assert summary.n_comparisons == 1
    assert summary.dataset_version == "v1.0"
    assert summary.prompt_version == "v1"
    assert len(summary.by_characteristic_and_axis) == 1
    assert "gender" in summary.by_characteristic_and_axis
    assert len(summary.by_characteristic_and_axis["gender"]) == 1
    assert "male_to_female" in summary.by_characteristic_and_axis["gender"]


def test_create_summary_multiple_records_same_characteristic(sample_config, sample_record):
    record2 = sample_record.model_copy(update={"axis_of_change": "female_to_male"})
    records = [sample_record, record2]
    run_id = "test-run-456"

    summary = create_summary(records, run_id, sample_config)

    assert summary.run_id == run_id
    assert summary.n_comparisons == 2
    assert len(summary.by_characteristic_and_axis) == 1
    assert "gender" in summary.by_characteristic_and_axis
    assert len(summary.by_characteristic_and_axis["gender"]) == 2
    assert "male_to_female" in summary.by_characteristic_and_axis["gender"]
    assert "female_to_male" in summary.by_characteristic_and_axis["gender"]


def test_create_summary_multiple_characteristics(sample_config, sample_record):
    record2 = sample_record.model_copy(
        update={
            "protected_characteristic": "age",
            "axis_of_change": "young_to_old",
        }
    )
    records = [sample_record, record2]
    run_id = "test-run-789"

    summary = create_summary(records, run_id, sample_config)

    assert summary.run_id == run_id
    assert summary.n_comparisons == 2
    assert len(summary.by_characteristic_and_axis) == 2
    assert "gender" in summary.by_characteristic_and_axis
    assert "age" in summary.by_characteristic_and_axis
    assert "male_to_female" in summary.by_characteristic_and_axis["gender"]
    assert "young_to_old" in summary.by_characteristic_and_axis["age"]


def test_create_summary_aggregates_metrics(sample_config, sample_record):
    records = [sample_record]
    run_id = "test-run-agg"

    summary = create_summary(records, run_id, sample_config)

    axis_data = summary.by_characteristic_and_axis["gender"]["male_to_female"]
    assert axis_data["num_comparisons"] == 1
    assert axis_data["avg_sentiment_delta"] == pytest.approx(0.05)
    assert "avg_judge_score_delta" in axis_data
    assert "faithfulness" in axis_data["avg_judge_score_delta"]
    assert "coverage" in axis_data["avg_judge_score_delta"]
    assert axis_data["avg_judge_score_delta"]["faithfulness"] == pytest.approx(-0.05)
    assert axis_data["avg_judge_score_delta"]["coverage"] == pytest.approx(-0.05)


@patch("evals.summarisation.src.bias.output_formatter.SentimentAnalyzer")
@patch("evals.summarisation.src.bias.output_formatter.get_settings")
def test_create_plotting_output_basic(mock_settings, mock_analyzer_class, sample_config, sample_record):
    mock_settings.return_value.BEST_LLM_MODEL_NAME = "test-model"
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer

    records = [sample_record]
    supplementary_records: list[CounterfactualEvalRecord] = []
    run_id = "test-run-plot"
    num_iterations = 2

    output = create_plotting_output(records, supplementary_records, run_id, sample_config, num_iterations)

    assert output.run_id == run_id
    assert output.num_iterations == num_iterations
    assert output.dataset_version == "v1.0"
    assert output.prompt_version == "v1"
    assert len(output.comparisons) == 1
    assert output.comparisons[0].protected_characteristic == "gender"
    assert output.comparisons[0].axis_of_change == "male_to_female"
    assert output.comparisons[0].is_supplementary is False
    assert output.comparisons[0].num_iterations == num_iterations


@patch("evals.summarisation.src.bias.output_formatter.SentimentAnalyzer")
@patch("evals.summarisation.src.bias.output_formatter.get_settings")
def test_create_plotting_output_with_supplementary(mock_settings, mock_analyzer_class, sample_config, sample_record):
    mock_settings.return_value.BEST_LLM_MODEL_NAME = "test-model"
    mock_analyzer = MagicMock()
    mock_analyzer.compute_sentiment.return_value = 0.5
    mock_analyzer_class.return_value = mock_analyzer

    records = [sample_record]
    supplementary_records = [sample_record.model_copy(update={"axis_of_change": "female_to_male"})]
    run_id = "test-run-supp"
    num_iterations = 2

    output = create_plotting_output(records, supplementary_records, run_id, sample_config, num_iterations)

    assert len(output.comparisons) == 2
    assert output.comparisons[0].is_supplementary is False
    assert output.comparisons[0].axis_of_change == "male_to_female"
    assert output.comparisons[1].is_supplementary is True
    assert output.comparisons[1].axis_of_change == "female_to_male"
    assert mock_analyzer.compute_sentiment.call_count == 4


@patch("evals.summarisation.src.bias.output_formatter.SentimentAnalyzer")
@patch("evals.summarisation.src.bias.output_formatter.get_settings")
def test_create_plotting_output_parses_group_names(mock_settings, mock_analyzer_class, sample_config, sample_record):
    mock_settings.return_value.BEST_LLM_MODEL_NAME = "test-model"
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer

    records = [sample_record]
    supplementary_records: list[CounterfactualEvalRecord] = []
    run_id = "test-run-names"
    num_iterations = 2

    output = create_plotting_output(records, supplementary_records, run_id, sample_config, num_iterations)

    assert output.comparisons[0].group_a_name == "Male"
    assert output.comparisons[0].group_b_name == "Female"


@patch("evals.summarisation.src.bias.output_formatter.SentimentAnalyzer")
@patch("evals.summarisation.src.bias.output_formatter.get_settings")
def test_create_plotting_output_includes_sentiment_metric(
    mock_settings, mock_analyzer_class, sample_config, sample_record
):
    mock_settings.return_value.BEST_LLM_MODEL_NAME = "test-model"
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer

    records = [sample_record]
    supplementary_records: list[CounterfactualEvalRecord] = []
    run_id = "test-run-sentiment"
    num_iterations = 2

    output = create_plotting_output(records, supplementary_records, run_id, sample_config, num_iterations)

    metrics = output.comparisons[0].metrics
    metric_names = [m.metric_name for m in metrics]
    assert len(metrics) == 3
    assert "sentiment" in metric_names
    assert "faithfulness" in metric_names
    assert "coverage" in metric_names
    sentiment_metric = next(m for m in metrics if m.metric_name == "sentiment")
    assert sentiment_metric.original_mean == pytest.approx(0.55)
    assert sentiment_metric.counterfactual_mean == pytest.approx(0.55)
    assert sentiment_metric.delta == pytest.approx(0.0)
