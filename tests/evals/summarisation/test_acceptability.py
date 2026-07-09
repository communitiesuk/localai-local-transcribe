"""
Tests the judge-score acceptability floor: checks the raw-4 -> normalised-0.75
threshold boundary is inclusive.

Exercises: evals.summarisation.src.acceptability.JudgeAcceptabilityClassifier.
"""

from __future__ import annotations

import pytest

from evals.summarisation.src.acceptability import JudgeAcceptabilityClassifier


@pytest.mark.parametrize(
    ("normalised", "acceptable"),
    [(1.0, True), (0.75, True), (0.749, False), (0.5, False), (0.0, False)],
)
def test_judge_acceptability_floor(normalised, acceptable):
    # raw 4 -> normalised (4-1)/4 = 0.75 is the floor
    assert JudgeAcceptabilityClassifier().is_acceptable(normalised) is acceptable
