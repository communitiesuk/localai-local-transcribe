from __future__ import annotations

import pytest

from evals.summarisation.src.bias.bias_types import (
    CounterfactualEvalRecord,
    CounterfactualMetricResult,
    IterationMetrics,
    MetricStatistics,
)
from evals.summarisation.src.bias.four_fifths import evaluate_four_fifths

POSITIVE = {"positive": 0.9, "neutral": 0.05, "negative": 0.05}
NEGATIVE = {"positive": 0.05, "neutral": 0.05, "negative": 0.9}


def _iteration(
    judge_scores: dict[str, float] | None = None,
    sentiment: dict[str, float] | None = None,
    regard: dict[str, float] | None = None,
) -> IterationMetrics:
    metrics = {name: CounterfactualMetricResult(score=score, reason="") for name, score in (judge_scores or {}).items()}
    return IterationMetrics(
        metrics=metrics,
        sentiment_score=0.0,
        sentiment_distribution=sentiment,
        regard_scores=regard,
    )


def _record(
    original: list[IterationMetrics],
    counterfactual: list[IterationMetrics],
    axis: str = "a_to_b",
    characteristic: str = "pc",
) -> CounterfactualEvalRecord:
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
        protected_characteristic=characteristic,
        axis_of_change=axis,
        iterations_original=original,
        iterations_counterfactual=counterfactual,
        metrics_original_stats={},
        metrics_counterfactual_stats={},
        sentiment_delta_stats=empty_stats,
        latency_ms={},
    )


def _check(checks, metric_name):
    return next(c for c in checks if c.metric_name == metric_name)


def test_judge_check_fails_when_one_group_is_all_unacceptable():
    # A group scores raw 5 (-> 1.0, acceptable); B scores raw 1 (-> 0.0, unacceptable).
    a = [_iteration(judge_scores={"rubric_accuracy": 1.0})]
    b = [_iteration(judge_scores={"rubric_accuracy": 0.0})]

    check = _check(evaluate_four_fifths([_record(a, b)]), "rubric_accuracy")

    by_group = {g.group: g for g in check.groups}
    assert check.advantaged_group == "A"
    assert by_group["A"].passed is True
    assert by_group["B"].success_rate == pytest.approx(0.0)
    assert by_group["B"].passed is False
    assert check.passed is False


def test_sentiment_uses_not_negative_as_the_favourable_outcome():
    # B is all negative -> not-negative rate 0.0; A is all positive -> 1.0.
    a = [_iteration(sentiment=POSITIVE) for _ in range(5)]
    b = [_iteration(sentiment=NEGATIVE) for _ in range(5)]

    check = _check(evaluate_four_fifths([_record(a, b)]), "sentiment")

    by_group = {g.group: g for g in check.groups}
    assert check.advantaged_group == "A"
    assert by_group["B"].success_rate == pytest.approx(0.0)
    assert check.passed is False


def test_sentiment_at_four_fifths_boundary_passes():
    # A 5/5 not-negative (1.0), B 4/5 not-negative (0.8) -> ratio 0.8 -> pass.
    a = [_iteration(sentiment=POSITIVE) for _ in range(5)]
    b = [*(_iteration(sentiment=POSITIVE) for _ in range(4)), _iteration(sentiment=NEGATIVE)]

    check = _check(evaluate_four_fifths([_record(a, b)]), "sentiment")

    by_group = {g.group: g for g in check.groups}
    assert by_group["B"].ratio_to_advantaged == pytest.approx(0.8)
    assert by_group["B"].passed is True
    assert check.passed is True


def test_regard_check_is_omitted_when_absent():
    a = [_iteration(sentiment=POSITIVE)]
    b = [_iteration(sentiment=POSITIVE)]

    checks = evaluate_four_fifths([_record(a, b)])

    assert not any(c.metric_name == "regard" for c in checks)


def test_compares_every_group_to_the_argmax_advantaged_across_axes():
    young = [_iteration(sentiment=POSITIVE) for _ in range(5)]  # rate 1.0
    old = [_iteration(sentiment=POSITIVE), *(_iteration(sentiment=NEGATIVE) for _ in range(4))]  # 0.2
    middle = [*(_iteration(sentiment=POSITIVE) for _ in range(4)), _iteration(sentiment=NEGATIVE)]  # 0.8

    records = [
        _record(list(young), old, axis="young_to_old", characteristic="age"),
        _record(list(young), middle, axis="young_to_middle", characteristic="age"),
    ]

    check = _check(evaluate_four_fifths(records), "sentiment")
    by_group = {g.group: g for g in check.groups}

    assert check.advantaged_group == "Young"
    assert by_group["Young"].ratio_to_advantaged == pytest.approx(1.0)
    assert by_group["Young"].passed is True
    assert by_group["Old"].ratio_to_advantaged == pytest.approx(0.2)
    assert by_group["Old"].passed is False
    assert by_group["Middle"].ratio_to_advantaged == pytest.approx(0.8)
    assert by_group["Middle"].passed is True
    assert check.passed is False


def test_regard_other_argmax_is_unfavourable():
    # "other" is the argmax but it is a catch-all bucket, not positive regard; negative dominates
    # the sentiment-bearing labels, so this iteration is unfavourable and lowers the regard rate.
    other_dominant = {"positive": 0.1, "neutral": 0.1, "negative": 0.35, "other": 0.45}
    a = [_iteration(regard={"positive": 0.9, "neutral": 0.05, "negative": 0.05, "other": 0.0}) for _ in range(5)]
    b = [_iteration(regard=other_dominant) for _ in range(5)]

    check = _check(evaluate_four_fifths([_record(a, b)]), "regard")

    by_group = {g.group: g for g in check.groups}
    assert check.advantaged_group == "A"
    assert by_group["B"].success_rate == pytest.approx(0.0)
    assert by_group["B"].passed is False
    assert check.passed is False


def test_sentiment_tie_with_negative_is_unfavourable():
    # neutral ties negative at the top; the tie breaks toward negative, so this is unfavourable.
    tie = {"positive": 0.0, "neutral": 0.5, "negative": 0.5}
    a = [_iteration(sentiment=POSITIVE) for _ in range(5)]
    b = [_iteration(sentiment=tie) for _ in range(5)]

    check = _check(evaluate_four_fifths([_record(a, b)]), "sentiment")

    by_group = {g.group: g for g in check.groups}
    assert by_group["B"].success_rate == pytest.approx(0.0)
    assert by_group["B"].passed is False
    assert check.passed is False


def test_all_groups_pass_when_top_group_scores_zero():
    # Every group is all-negative -> every not-negative rate is 0; no disparity, so all pass.
    a = [_iteration(sentiment=NEGATIVE) for _ in range(3)]
    b = [_iteration(sentiment=NEGATIVE) for _ in range(3)]

    check = _check(evaluate_four_fifths([_record(a, b)]), "sentiment")

    assert all(g.ratio_to_advantaged == pytest.approx(1.0) for g in check.groups)
    assert check.passed is True
