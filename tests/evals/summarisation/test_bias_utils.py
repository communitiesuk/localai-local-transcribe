from __future__ import annotations

import pytest

from common.database.postgres_models import DialogueEntry
from evals.summarisation.src.bias.types import CounterfactualMetricResult, IterationMetrics
from evals.summarisation.src.bias.utils import (
    compute_comparison_statistics,
    compute_metric_statistics,
    compute_statistics,
    format_dialogue,
    parse_group_names,
)


def test_format_dialogue_single_entry():
    dialogue_entries = [{"speaker": "1", "text": "Hello world"}]
    result = format_dialogue(dialogue_entries)
    assert result == "Speaker 1: Hello world"


def test_format_dialogue_multiple_entries():
    dialogue_entries = [
        {"speaker": "1", "text": "Hello"},
        {"speaker": "2", "text": "Hi there"},
        {"speaker": "1", "text": "How are you?"},
    ]
    result = format_dialogue(dialogue_entries)
    expected = "Speaker 1: Hello\nSpeaker 2: Hi there\nSpeaker 1: How are you?"
    assert result == expected


def test_format_dialogue_empty_list():
    dialogue_entries: list[DialogueEntry] = []
    result = format_dialogue(dialogue_entries)
    assert result == ""


def test_parse_group_names_basic():
    axis_of_change = "male_to_female"
    group_a, group_b = parse_group_names(axis_of_change)
    assert group_a == "Male"
    assert group_b == "Female"


def test_parse_group_names_multi_word():
    axis_of_change = "young_person_to_older_person"
    group_a, group_b = parse_group_names(axis_of_change)
    assert group_a == "Young Person"
    assert group_b == "Older Person"


def test_parse_group_names_single_word():
    axis_of_change = "white_to_black"
    group_a, group_b = parse_group_names(axis_of_change)
    assert group_a == "White"
    assert group_b == "Black"


def test_compute_statistics_basic():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = compute_statistics(values)
    assert result.mean == pytest.approx(3.0)
    assert result.std == pytest.approx(1.5811388300841898)
    assert result.values == values
    assert len(result.values) == 5


def test_compute_statistics_single_value():
    values = [5.0]
    result = compute_statistics(values)
    assert result.mean == 5.0
    assert result.std == 0.0
    assert result.values == values


def test_compute_statistics_two_values():
    values = [2.0, 4.0]
    result = compute_statistics(values)
    assert result.mean == pytest.approx(3.0)
    assert result.std == pytest.approx(1.4142135623730951)
    assert result.values == values
    assert len(result.values) == 2


def test_compute_metric_statistics_single_metric():
    iterations = [
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
            sentiment_score=0.5,
        ),
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.9, reason="Great")},
            sentiment_score=0.6,
        ),
    ]
    result = compute_metric_statistics(iterations)
    assert "faithfulness" in result
    assert len(result) == 1
    assert result["faithfulness"].mean == pytest.approx(0.85)
    assert result["faithfulness"].std == pytest.approx(0.07071067811865476)
    assert result["faithfulness"].values == pytest.approx([0.8, 0.9])
    assert len(result["faithfulness"].values) == 2


def test_compute_metric_statistics_multiple_metrics():
    iterations = [
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
    result = compute_metric_statistics(iterations)
    assert len(result) == 2
    assert "faithfulness" in result
    assert "coverage" in result
    assert result["faithfulness"].mean == pytest.approx(0.85)
    assert result["faithfulness"].std == pytest.approx(0.07071067811865476)
    assert result["faithfulness"].values == pytest.approx([0.8, 0.9])
    assert result["coverage"].mean == pytest.approx(0.75)
    assert result["coverage"].std == pytest.approx(0.07071067811865476)
    assert result["coverage"].values == pytest.approx([0.7, 0.8])


def test_compute_comparison_statistics_basic():
    original_iterations = [
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
            sentiment_score=0.5,
        ),
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.9, reason="Great")},
            sentiment_score=0.6,
        ),
    ]
    cf_iterations = [
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.7, reason="OK")},
            sentiment_score=0.4,
        ),
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
            sentiment_score=0.5,
        ),
    ]
    result = compute_comparison_statistics(original_iterations, cf_iterations)
    assert result.mean == pytest.approx(-0.1)
    assert result.std == pytest.approx(0.0)
    assert len(result.values) == 2
    assert result.values == pytest.approx([-0.1, -0.1])


def test_compute_comparison_statistics_positive_delta():
    original_iterations = [
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.5, reason="OK")},
            sentiment_score=0.3,
        ),
    ]
    cf_iterations = [
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.7, reason="Good")},
            sentiment_score=0.7,
        ),
    ]
    result = compute_comparison_statistics(original_iterations, cf_iterations)
    assert result.mean == pytest.approx(0.4)
    assert result.std == pytest.approx(0.0)
    assert len(result.values) == 1
    assert result.values == pytest.approx([0.4])


def test_compute_statistics_empty_list():
    with pytest.raises(ValueError, match="Cannot compute statistics on empty list"):
        compute_statistics([])


def test_compute_metric_statistics_empty_iterations():
    with pytest.raises(ValueError, match="Cannot compute metric statistics on empty iterations list"):
        compute_metric_statistics([])


def test_compute_metric_statistics_mismatched_keys():
    iterations = [
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
            sentiment_score=0.5,
        ),
        IterationMetrics(
            metrics={"coverage": CounterfactualMetricResult(score=0.7, reason="OK")},
            sentiment_score=0.6,
        ),
    ]
    with pytest.raises(KeyError):
        compute_metric_statistics(iterations)


def test_compute_comparison_statistics_mismatched_lengths():
    original_iterations = [
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
            sentiment_score=0.5,
        ),
    ]
    cf_iterations = [
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.7, reason="OK")},
            sentiment_score=0.4,
        ),
        IterationMetrics(
            metrics={"faithfulness": CounterfactualMetricResult(score=0.8, reason="Good")},
            sentiment_score=0.5,
        ),
    ]
    with pytest.raises(ValueError, match="zip"):
        compute_comparison_statistics(original_iterations, cf_iterations)


def test_parse_group_names_no_separator():
    with pytest.raises(ValueError, match="Invalid axis_of_change format"):
        parse_group_names("male_female")


def test_parse_group_names_multiple_separators():
    axis_of_change = "young_to_middle_to_old"
    with pytest.raises(ValueError, match="Invalid axis_of_change format"):
        parse_group_names(axis_of_change)
