from typing import Literal, NamedTuple

# Judge rubric scores are stored normalised to [0, 1] from the raw 1-5 rubric scale.
JUDGE_RAW_MIN = 1.0
JUDGE_RAW_MAX = 5.0


def normalise_judge_score(raw: float) -> float:
    """Map a raw judge score on the 1-5 rubric scale to [0, 1] (out-of-range inputs are clamped)."""
    clamped = min(max(raw, JUDGE_RAW_MIN), JUDGE_RAW_MAX)
    return (clamped - JUDGE_RAW_MIN) / (JUDGE_RAW_MAX - JUDGE_RAW_MIN)


DIMENSIONS_LABELS: dict[str, str] = {
    "accuracy": "Factual Accuracy",
    "numerical_accuracy": "Numeric Fidelity",
    "template_fit": "Template Adherence & Completeness",
    "coverage": "Transcript Factual Completeness",
    "action_clarity": "Actionability",
    "professional_tone": "Tone",
    "readability": "Structure & Readability",
    "auditability": "Citation Quality",
}

DIMENSIONS = DIMENSIONS_LABELS

THRESHOLDS = {
    "critical": 4,
    "review": 2,
    "fail": 1,
}

HALLUCINATION_GATED_DIMENSIONS = {
    "accuracy",
    "numerical_accuracy",
    "action_clarity",
}

CRITICAL_DIMENSIONS = frozenset(HALLUCINATION_GATED_DIMENSIONS)
CRITICAL_THRESHOLD = THRESHOLDS["critical"]
REVIEW_THRESHOLD = THRESHOLDS["review"]
FAIL_THRESHOLD = THRESHOLDS["fail"]
MAX_SCORE_DRIFT = 0.15
MIN_SCORE = 1
MAX_SCORE = 5
MIN_RATIONALE_LENGTH = 20
CONCURRENCY = 4


class ScoreBand(NamedTuple):
    """Pass, review, and fail boundaries for one judge dimension on the 1 to 5 scale.

    The LLM judge scores each dimension as an integer from 1 (worst) to 5 (best). A band
    turns that raw score into one of three actions for the offline evaluation pipeline:

    pass_minimum: the lowest score that passes with no action required.
    review_score: the single score that falls into the eval review band for analyst inspection.
    fail_maximum: the highest score that counts as a failed evaluation.

    The three actions cover the whole scale with no gaps. For the strict setting
    (4, 3, 2) a score of 5 or 4 passes, 3 is reviewed, and 2 or 1 fails. For the standard
    setting (3, 2, 1) a score of 3, 4, or 5 passes, 2 is reviewed, and 1 fails.
    """

    pass_minimum: int
    review_score: int
    fail_maximum: int


# Every threshold value below is a calibration placeholder. We do not yet have human-labelled
# summaries to calibrate against, so these are risk-based defaults rather than values
# derived from data. The full rationale is detailed in documentation/llm-judge-score-thresholds.md.
# Downstream code and reviewers can read this flag to confirm the numbers are provisional and
# pending dataset calibration.
THRESHOLDS_ARE_CALIBRATION_PLACEHOLDERS = True

# The two threshold settings, shared so each value is written once. These name the numbers,
# not a group of dimensions: which dimensions use which setting is decided in
# DIMENSION_SCORE_BANDS below. The strict setting has a high pass bar (4) for dimensions
# where a low score is high harm and an end user reviewing the draft in the product is
# unlikely to catch the failure.
STRICT_BAND = ScoreBand(pass_minimum=4, review_score=3, fail_maximum=2)

# The standard setting has a pass bar one point lower (3). It is used for dimensions where
# a low score is lower harm, visible on the page, or fixable by editing before adoption.
STANDARD_BAND = ScoreBand(pass_minimum=3, review_score=2, fail_maximum=1)

# Per-dimension thresholds. This mapping is the single source of truth for the thresholds
# work and supersedes the flat THRESHOLDS dict above (which is kept because other modules
# still import it and enforcement is a separate, later story). Full rationale:
# documentation/llm-judge-score-thresholds.md (AIILG-678).
DIMENSION_SCORE_BANDS: dict[str, ScoreBand] = {
    "accuracy": STRICT_BAND,
    "numerical_accuracy": STRICT_BAND,
    "action_clarity": STRICT_BAND,
    "coverage": STRICT_BAND,  # omission risk. end users rarely spot missing content. not hallucination-gated
    "auditability": STANDARD_BAND,  # arguably pass 4, but kept standard. may want to revisit after calibration
    "template_fit": STANDARD_BAND,
    "readability": STANDARD_BAND,  # formatting and render-safety only. low harm and visible on the page
    "professional_tone": STANDARD_BAND,
}


class CitationRateBand(NamedTuple):
    """Pass and review boundaries for the claim citation rate, as proportions in the range 0 to 1.

    The claim citation rate is the proportion of a summary's extracted claims that were matched
    to at least one transcript entry, that is n_supported divided by total_claims. It runs from
    0.0 (no claim could be cited) to 1.0 (every claim could be cited). A band turns that rate
    into one of three actions for the offline evaluation pipeline:

    pass_minimum: the lowest citation rate that passes with no action required.
    review_minimum: the lowest citation rate that still falls in the review band. A rate below
        this value is a fail.

    The two boundaries cover the whole range with no gaps. For the placeholder band
    (0.95, 0.85) a rate of 0.95 or above passes, a rate from 0.85 up to but not including 0.95
    is reviewed, and a rate below 0.85 fails.
    """

    pass_minimum: float
    review_minimum: float


# The claim citation rate thresholds are calibration placeholders, mirroring the judge-score
# flag above. We do not yet have human-labelled transcript-support data to calibrate against,
# so these are risk-based defaults rather than values derived from data. Full rationale:
# documentation/eval_thresholds/claim-citation-rate-thresholds.md (AIILG-679).
CITATION_RATE_THRESHOLDS_ARE_CALIBRATION_PLACEHOLDERS = True

# Placeholder pass and review boundaries for the per-summary claim citation rate.
# TODO(AIILG-679): 0.95 pass and 0.85 review are placeholders. Replace them once the metric has
# been calibrated against human judgements of whether each extracted claim is supported.
# https://mhclgdigital.atlassian.net/browse/AIILG-679
# The pass bar is set higher than the ticket's suggested 90/80 rate because an uncited
# claim is a strong signal that something is off. ie the citation step is instructed to cite anything
# with even partial support, and the summaries feed high-consequence statutory workflows.
# The review band is kept wide because the rate is itself produced by two LLM steps (claim extraction and
# citation) whose error is not yet measured. A decision should be taken from the raw counts
# (n_supported over total_claims), not from the rate after it has been rounded for display, so
# that a value on a boundary is not moved by rounding. This is why the review band is wider than the pass band.
CITATION_RATE_BAND = CitationRateBand(pass_minimum=0.95, review_minimum=0.85)

CitationOutcome = Literal["pass", "review", "fail"]

# How to treat a summary from which no claims were extracted (total_claims == 0). The citation
# rate is undefined in that case (a division of zero by zero), so such a summary must never
# count as a pass by default. It is routed to the review band for human inspection instead.
CITATION_RATE_ZERO_CLAIMS_POLICY: CitationOutcome = "review"


def citation_rate_outcome(
    n_supported: int,
    total_claims: int,
    band: CitationRateBand = CITATION_RATE_BAND,
) -> CitationOutcome:
    """Score a summary's claim citation rate against the pass/review/fail bands.

    The decision is taken from the raw counts (n_supported over total_claims) rather than
    the rounded rate, so a value sitting on a band boundary is not moved by rounding. A
    summary with no extracted claims (total_claims == 0) has an undefined rate and is
    routed to review per CITATION_RATE_ZERO_CLAIMS_POLICY, never an automatic pass.
    """
    if total_claims <= 0:
        return CITATION_RATE_ZERO_CLAIMS_POLICY
    if n_supported >= band.pass_minimum * total_claims:
        return "pass"
    if n_supported >= band.review_minimum * total_claims:
        return "review"
    return "fail"
