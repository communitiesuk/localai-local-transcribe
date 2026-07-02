from __future__ import annotations

import pytest

from evals.summarisation.src.common.metric import DialogSummaryMetric
from evals.summarisation.src.constants import (
    JUDGE_RAW_MAX,
    JUDGE_RAW_MIN,
    normalise_judge_score,
)

# --- normalise_judge_score (single source of truth for raw 1-5 -> [0, 1]) ---


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(1.0, 0.0), (2.0, 0.25), (3.0, 0.5), (4.0, 0.75), (5.0, 1.0)],
)
def test_normalise_maps_raw_scale_to_unit_interval(raw, expected):
    assert normalise_judge_score(raw) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(0.0, 0.0), (-1.0, 0.0), (6.0, 1.0), (10.0, 1.0)],
)
def test_normalise_clamps_out_of_range_inputs(raw, expected):
    assert normalise_judge_score(raw) == pytest.approx(expected)


def test_normalise_endpoints_use_the_scale_constants():
    assert normalise_judge_score(JUDGE_RAW_MIN) == pytest.approx(0.0)
    assert normalise_judge_score(JUDGE_RAW_MAX) == pytest.approx(1.0)


# --- DialogSummaryMetric._build_result scales via the shared helper ---


def _rubric(dim: str, score: int) -> dict:
    return {"dimensions": {dim: {"score": score, "rationale": "because"}}}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(1, 0.0), (4, 0.75), (5, 1.0)],
)
def test_build_result_normalises_score(raw, expected):
    metric = DialogSummaryMetric(name="accuracy", criterion="", pass_threshold=4)

    result = metric._build_result("accuracy", _rubric("accuracy", raw))  # noqa: SLF001

    assert result.score == pytest.approx(normalise_judge_score(raw))
    assert result.score == pytest.approx(expected)
