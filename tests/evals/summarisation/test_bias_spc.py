"""
Tests the SPC checks: baseline loading/validation, control-limit pass/fail, and
the narrowed-toward-zero exception.

Exercises: evals.summarisation.src.bias.spc (load_spc_baseline, check_metric,
evaluate_spc).
"""

from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from evals.summarisation.src.bias.bias_types import ComparisonMetrics, ComparisonResult, MetricStatistics
from evals.summarisation.src.bias.constants import SPC_BASELINE_FILENAME
from evals.summarisation.src.bias.spc import (
    build_spc_baseline,
    check_metric,
    evaluate_spc,
    load_spc_baseline,
    save_spc_baseline,
)
from evals.summarisation.src.bias.spc_types import SPCBaseline, SPCBaselineStat


@pytest.fixture
def baseline() -> SPCBaseline:
    return SPCBaseline(
        metrics={
            "sentiment": {"mean": 0.2, "std": 0.05},
            "rubric_accuracy": {"mean": 0.0, "std": 0.05},
        },
    )


def _comparison(metric_name: str, delta: float) -> ComparisonMetrics:
    return ComparisonMetrics(
        metric_name=metric_name,
        original_mean=0.0,
        original_std=0.0,
        counterfactual_mean=delta,
        counterfactual_std=0.0,
        delta=delta,
        original_values=[],
        counterfactual_values=[],
    )


def test_delta_within_limits_passes(baseline):
    # limits for sentiment: 0.2 +/- 0.15 -> [0.05, 0.35]
    check = check_metric("sentiment", 0.25, baseline)
    assert check is not None
    assert check.passed is True
    assert check.lower_limit == pytest.approx(0.05)
    assert check.upper_limit == pytest.approx(0.35)


def test_widened_gap_fails(baseline):
    # 0.6 is above the upper limit and further from zero than the baseline mean
    check = check_metric("sentiment", 0.6, baseline)
    assert check.passed is False


def test_reversed_gap_fails(baseline):
    # large reversal: opposite sign, magnitude beyond the baseline gap
    check = check_metric("sentiment", -0.5, baseline)
    assert check.passed is False


def test_narrowing_toward_zero_passes(baseline):
    # 0.0 breaches the lower limit (0.05) but the gap has shrunk toward zero -> pass (improvement)
    check = check_metric("sentiment", 0.0, baseline)
    assert check.passed is True


def test_equal_magnitude_reversal_fails():
    # A sign-flip of equal magnitude is a reversal, not an improvement.
    baseline = SPCBaseline(metrics={"sentiment": {"mean": 0.5, "std": 0.05}})
    check = check_metric("sentiment", -0.5, baseline)
    assert check.passed is False


def test_reversal_with_negative_baseline_mean_fails():
    baseline = SPCBaseline(metrics={"sentiment": {"mean": -0.5, "std": 0.1}})
    check = check_metric("sentiment", 0.5, baseline)
    assert check.passed is False


def test_partial_narrowing_same_side_passes():
    # Same sign as baseline, smaller magnitude, outside the limits -> improvement.
    baseline = SPCBaseline(metrics={"sentiment": {"mean": 0.5, "std": 0.05}})
    check = check_metric("sentiment", 0.1, baseline)
    assert check.passed is True


def test_zero_std_baseline_is_rejected():
    # A zero-variance baseline collapses the control band; reject it at load time.
    with pytest.raises(ValidationError):
        SPCBaselineStat(mean=0.3, std=0.0)


def test_metric_without_baseline_entry_is_skipped(baseline):
    assert check_metric("rubric_coverage", 0.9, baseline) is None


def test_evaluate_spc_checks_each_metric_with_a_baseline(baseline):
    comparisons = [_comparison("sentiment", 0.25), _comparison("rubric_accuracy", 0.5)]
    checks = evaluate_spc(comparisons, baseline)
    assert [c.passed for c in checks] == [True, False]


def test_evaluate_spc_skips_metrics_absent_from_baseline(baseline):
    checks = evaluate_spc([_comparison("unknown_metric", 0.9)], baseline)
    assert checks == []


def test_load_spc_baseline_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="required input"):
        load_spc_baseline(tmp_path)


def test_load_spc_baseline_malformed_raises(tmp_path):
    (tmp_path / SPC_BASELINE_FILENAME).write_text(
        yaml.safe_dump({"metrics": {"sentiment": {"mean": 0.1}}}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_spc_baseline(tmp_path)


def test_load_spc_baseline_reads_file(tmp_path):
    payload = {"metrics": {"sentiment": {"mean": 0.1, "std": 0.02}}}
    (tmp_path / SPC_BASELINE_FILENAME).write_text(yaml.safe_dump(payload), encoding="utf-8")

    baseline = load_spc_baseline(tmp_path)

    assert baseline.metrics["sentiment"].mean == pytest.approx(0.1)


def _comparison_result(deltas: dict[str, float]) -> ComparisonResult:
    empty = MetricStatistics(mean=0.0, std=0.0, values=[])
    return ComparisonResult(
        comparison_id="c",
        protected_characteristic="gender",
        axis_of_change="male_to_female",
        group_a_name="Male",
        group_b_name="Female",
        metrics=[_comparison(name, delta) for name, delta in deltas.items()],
        sentiment_delta=empty,
        sentiment_distribution_original=[],
        sentiment_distribution_counterfactual=[],
        num_iterations=1,
        hypothesis_model="m",
        prompt_version="v",
    )


def test_build_spc_baseline_computes_mean_and_std():
    comparisons = [
        _comparison_result({"sentiment": 0.1}),
        _comparison_result({"sentiment": 0.3}),
        _comparison_result({"sentiment": 0.2}),
    ]

    baseline = build_spc_baseline(comparisons)

    assert baseline.metrics["sentiment"].mean == pytest.approx(0.2)
    assert baseline.metrics["sentiment"].std == pytest.approx(0.1)


def test_build_spc_baseline_skips_single_observation_metric():
    # "sentiment" has two observations; "regard" appears once -> not enough to form a band.
    comparisons = [
        _comparison_result({"sentiment": 0.1, "regard": 0.5}),
        _comparison_result({"sentiment": 0.3}),
    ]

    baseline = build_spc_baseline(comparisons)

    assert "sentiment" in baseline.metrics
    assert "regard" not in baseline.metrics


def test_build_spc_baseline_skips_zero_variance_metric():
    comparisons = [_comparison_result({"sentiment": 0.2}), _comparison_result({"sentiment": 0.2})]

    with pytest.raises(ValueError, match="no metric"):
        build_spc_baseline(comparisons)


def test_save_spc_baseline_round_trips_through_load(tmp_path):
    comparisons = [
        _comparison_result({"sentiment": 0.1}),
        _comparison_result({"sentiment": 0.3}),
    ]
    baseline = build_spc_baseline(comparisons, description="test run")

    path = save_spc_baseline(baseline, tmp_path)

    assert path == tmp_path / SPC_BASELINE_FILENAME
    reloaded = load_spc_baseline(tmp_path)
    assert reloaded.metrics["sentiment"].mean == pytest.approx(0.2)
    assert reloaded.description == "test run"
