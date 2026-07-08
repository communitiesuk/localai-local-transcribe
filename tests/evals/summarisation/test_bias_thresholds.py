"""
Tests threshold application end to end: attaching SPC and 4/5 verdicts to a built
output and the has_threshold_failures exit-code signal.

Exercises: evals.summarisation.src.bias.thresholds (apply_thresholds,
has_threshold_failures).
"""

from __future__ import annotations

from evals.summarisation.src.bias.bias_types import (
    BiasEvalResults,
    ComparisonMetrics,
    ComparisonResult,
    CounterfactualEvalRecord,
    IterationMetrics,
    MetricStatistics,
)
from evals.summarisation.src.bias.spc_types import SPCBaseline
from evals.summarisation.src.bias.thresholds import apply_thresholds, has_threshold_failures

POSITIVE = {"positive": 0.9, "neutral": 0.05, "negative": 0.05}
NEGATIVE = {"positive": 0.05, "neutral": 0.05, "negative": 0.9}


def _sentiment_iteration(distribution: dict[str, float]) -> IterationMetrics:
    return IterationMetrics(metrics={}, sentiment_score=0.0, sentiment_distribution=distribution)


def _record(original, counterfactual) -> CounterfactualEvalRecord:
    empty_stats = MetricStatistics(mean=0.0, std=0.0, values=[])
    return CounterfactualEvalRecord(
        run_id="r",
        timestamp="t",
        example_id="e",
        transcription_text_original="",
        transcription_text_counterfactual="",
        hypothesis_summaries_original=[],
        hypothesis_summaries_counterfactual=[],
        hypothesis_model="m",
        prompt_version="v",
        protected_characteristic="gender",
        axis_of_change="male_to_female",
        iterations_original=original,
        iterations_counterfactual=counterfactual,
        metrics_original_stats={},
        metrics_counterfactual_stats={},
        sentiment_delta_stats=empty_stats,
        latency_ms={},
    )


def _comparison_result(delta: float) -> ComparisonResult:
    empty_stats = MetricStatistics(mean=0.0, std=0.0, values=[])
    return ComparisonResult(
        comparison_id="gender_male_to_female_0",
        protected_characteristic="gender",
        axis_of_change="male_to_female",
        group_a_name="Male",
        group_b_name="Female",
        is_supplementary=False,
        metrics=[
            ComparisonMetrics(
                metric_name="sentiment",
                original_mean=0.0,
                original_std=0.0,
                counterfactual_mean=delta,
                counterfactual_std=0.0,
                delta=delta,
                original_values=[],
                counterfactual_values=[],
            )
        ],
        sentiment_delta=empty_stats,
        sentiment_distribution_original=[],
        sentiment_distribution_counterfactual=[],
        num_iterations=1,
        hypothesis_model="m",
        prompt_version="v",
    )


def _output(record: ComparisonResult) -> BiasEvalResults:
    return BiasEvalResults(
        run_id="r",
        timestamp="t",
        dataset_version="v",
        engine_version="e",
        prompt_version="v",
        num_iterations=1,
        comparisons=[record],
    )


def test_apply_thresholds_attaches_spc_and_four_fifths():
    output = _output(_comparison_result(delta=0.25))
    records = [
        _record(
            original=[_sentiment_iteration(POSITIVE)],
            counterfactual=[_sentiment_iteration(NEGATIVE)],
        )
    ]
    baseline = SPCBaseline(metrics={"sentiment": {"mean": 0.2, "std": 0.05}})

    apply_thresholds(output, records, baseline)

    # SPC attached per comparison: 0.25 within [0.05, 0.35] -> pass.
    assert len(output.comparisons[0].spc_checks) == 1
    assert output.comparisons[0].spc_checks[0].passed is True

    # 4/5 attached at output level: Female is all-negative -> fails vs all-positive Male.
    sentiment = next(c for c in output.four_fifths if c.metric_name == "sentiment")
    assert sentiment.advantaged_group == "Male"
    assert sentiment.passed is False


def test_apply_thresholds_is_empty_start():
    # Fields default empty before the post step runs.
    output = _output(_comparison_result(delta=0.25))
    assert output.comparisons[0].spc_checks == []
    assert output.four_fifths == []


def _baseline() -> SPCBaseline:
    return SPCBaseline(metrics={"sentiment": {"mean": 0.2, "std": 0.05}})


def test_has_threshold_failures_true_when_four_fifths_fails():
    output = _output(_comparison_result(delta=0.25))  # SPC within limits -> passes
    records = [_record([_sentiment_iteration(POSITIVE)], [_sentiment_iteration(NEGATIVE)])]
    apply_thresholds(output, records, _baseline())

    assert output.comparisons[0].spc_checks[0].passed is True
    assert has_threshold_failures(output) is True


def test_has_threshold_failures_true_when_spc_fails():
    output = _output(_comparison_result(delta=0.9))  # far outside [0.05, 0.35] -> SPC fails
    records = [_record([_sentiment_iteration(POSITIVE)], [_sentiment_iteration(POSITIVE)])]
    apply_thresholds(output, records, _baseline())

    assert output.comparisons[0].spc_checks[0].passed is False
    assert all(c.passed for c in output.four_fifths)
    assert has_threshold_failures(output) is True


def test_has_threshold_failures_false_when_all_pass():
    output = _output(_comparison_result(delta=0.25))  # within limits
    records = [_record([_sentiment_iteration(POSITIVE)], [_sentiment_iteration(POSITIVE)])]
    apply_thresholds(output, records, _baseline())

    assert output.comparisons[0].spc_checks[0].passed is True
    assert all(c.passed for c in output.four_fifths)
    assert has_threshold_failures(output) is False
