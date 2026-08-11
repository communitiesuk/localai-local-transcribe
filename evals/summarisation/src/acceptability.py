"""
Judge-score acceptability: decides whether a normalised judge score (raw 1-5
rubric mapped to [0, 1]) clears the pass mark for its own dimension.

Each dimension carries its own pass mark, defined in constants.DIMENSION_SCORE_BANDS.
The strict setting passes at a raw score of 4 and the standard setting passes at a
raw score of 3, so the dimension has to be known before a score can be classified.

Pipeline: a shared primitive for the bias thresholds. The four-fifths rule uses it
to turn per-iteration judge scores into favourable/unfavourable outcomes.

Depends on: constants (DIMENSION_SCORE_BANDS, normalise_judge_score).
Depended on by: bias/four_fifths.py.
"""

from __future__ import annotations

from evals.summarisation.src.constants import DIMENSION_SCORE_BANDS, normalise_judge_score

# Recorded judge metrics are named with a "rubric_" prefix, for example "rubric_accuracy",
# whilst DIMENSION_SCORE_BANDS is keyed on the bare dimension name, for example "accuracy".
# The prefix is removed before the band is looked up.
RUBRIC_METRIC_PREFIX = "rubric_"


class JudgeAcceptabilityClassifier:
    """Whether a single judge score clears the pass mark for its dimension.

    Scores arrive normalised to [0, 1], so the pass mark is normalised onto the same
    scale before the two are compared.
    """

    def is_acceptable(self, normalised_score: float, metric_name: str) -> bool:
        """Whether the score clears the pass mark for the named dimension.

        metric_name may be given either with the "rubric_" prefix used by recorded
        metrics or as the bare dimension name. A dimension with no defined score band
        raises KeyError, because there is no pass mark to judge the score against.
        """
        band = DIMENSION_SCORE_BANDS[metric_name.removeprefix(RUBRIC_METRIC_PREFIX)]
        return normalised_score >= normalise_judge_score(band.pass_minimum)
