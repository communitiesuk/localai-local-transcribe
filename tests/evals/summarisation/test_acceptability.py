"""
Tests the judge-score pass marks: checks each dimension is held to the pass mark from
its own score band, and that a score sitting exactly on the pass mark is acceptable.
Also checks every judge dimension has a pass mark defined for it.

Exercises: evals.summarisation.src.acceptability.JudgeAcceptabilityClassifier.
"""

from __future__ import annotations

import pytest

from evals.summarisation.src.acceptability import JudgeAcceptabilityClassifier
from evals.summarisation.src.constants import DIMENSION_SCORE_BANDS, DIMENSIONS_LABELS


@pytest.mark.parametrize(
    ("normalised", "acceptable"),
    [(1.0, True), (0.75, True), (0.749, False), (0.5, False), (0.0, False)],
)
def test_strict_dimension_passes_at_raw_four(normalised, acceptable):
    # accuracy takes the strict band, so a raw 4 is the pass mark. It normalises to
    # (4 - 1) / 4 = 0.75.
    assert JudgeAcceptabilityClassifier().is_acceptable(normalised, "rubric_accuracy") is acceptable


@pytest.mark.parametrize(
    ("normalised", "acceptable"),
    [(1.0, True), (0.75, True), (0.5, True), (0.499, False), (0.0, False)],
)
def test_standard_dimension_passes_at_raw_three(normalised, acceptable):
    # auditability takes the standard band, so a raw 3 is the pass mark. It normalises to
    # (3 - 1) / 4 = 0.5. A raw 3 fails the strict band but passes here.
    assert JudgeAcceptabilityClassifier().is_acceptable(normalised, "rubric_auditability") is acceptable


def test_bare_dimension_name_is_accepted():
    # The prefix is optional so the classifier can be called with either naming style.
    assert JudgeAcceptabilityClassifier().is_acceptable(0.5, "auditability") is True


def test_unknown_dimension_raises():
    with pytest.raises(KeyError):
        JudgeAcceptabilityClassifier().is_acceptable(1.0, "rubric_not_a_dimension")


def test_every_judge_dimension_has_a_score_band():
    # The classifier raises when a dimension has no band. That would happen partway through a
    # bias run, once the summarisation and judge calls have already been paid for and before any
    # results are written. Checking the two mappings agree here means a dimension added without a
    # pass mark fails in CI instead. The reverse direction is checked too, so a band left behind
    # after a dimension is removed is also caught.
    dimensions_with_no_band = set(DIMENSIONS_LABELS) - set(DIMENSION_SCORE_BANDS)
    bands_with_no_dimension = set(DIMENSION_SCORE_BANDS) - set(DIMENSIONS_LABELS)

    assert not dimensions_with_no_band, f"judge dimensions with no pass mark: {sorted(dimensions_with_no_band)}"
    assert not bands_with_no_dimension, f"pass marks for unknown dimensions: {sorted(bands_with_no_dimension)}"
