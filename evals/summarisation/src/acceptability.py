from __future__ import annotations

from evals.summarisation.src.constants import JUDGE_ACCEPTABLE_RAW_MIN, normalise_judge_score


class JudgeAcceptabilityClassifier:
    """Whether a single judge score clears the acceptability floor.

    The floor defaults to a raw judge score of 4 on the 1-5 rubric scale. Scores
    arrive normalised to [0, 1], so the comparison happens in normalised space.
    """

    def __init__(self, raw_minimum: float = JUDGE_ACCEPTABLE_RAW_MIN) -> None:
        self._normalised_minimum = normalise_judge_score(raw_minimum)

    def is_acceptable(self, normalised_score: float) -> bool:
        return normalised_score >= self._normalised_minimum
