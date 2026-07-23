from __future__ import annotations

from evals.summarisation.src.constants import (
    CITATION_RATE_BAND,
    CITATION_RATE_ZERO_CLAIMS_POLICY,
    citation_rate_outcome,
)


def test_pass_at_and_above_pass_minimum():
    # 19/20 = 0.95 sits exactly on the pass boundary.
    assert citation_rate_outcome(n_supported=19, total_claims=20) == "pass"
    assert citation_rate_outcome(n_supported=20, total_claims=20) == "pass"


def test_review_between_bands():
    # 18/20 = 0.90 is below pass (0.95) but at or above review (0.85).
    assert citation_rate_outcome(n_supported=18, total_claims=20) == "review"
    # 17/20 = 0.85 sits exactly on the review boundary.
    assert citation_rate_outcome(n_supported=17, total_claims=20) == "review"


def test_fail_below_review_minimum():
    # 16/20 = 0.80 is below the review boundary (0.85).
    assert citation_rate_outcome(n_supported=16, total_claims=20) == "fail"


def test_zero_claims_routes_to_review_never_pass():
    outcome = citation_rate_outcome(n_supported=0, total_claims=0)
    assert outcome == CITATION_RATE_ZERO_CLAIMS_POLICY
    assert outcome == "review"


def test_decision_uses_raw_counts_not_rounded_rate():
    # 949/1000 = 0.949 rounds to 0.95 at three decimals but is genuinely below the
    # pass boundary, so the raw-count decision must be review, not pass.
    assert citation_rate_outcome(n_supported=949, total_claims=1000) == "review"


def test_placeholder_band_boundaries_are_the_ones_under_test():
    assert CITATION_RATE_BAND.pass_minimum == 0.95
    assert CITATION_RATE_BAND.review_minimum == 0.85
