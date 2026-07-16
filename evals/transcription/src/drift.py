"""Drift threshold checks for transcription eval metrics (AIILG-680)."""

from __future__ import annotations

from evals.transcription.src.constants import (
    SPEAKER_COUNT_DRIFT_THRESHOLDS,
    SpeakerCountDriftThresholds,
)


def require_speaker_count_recipe_size(
    run_meeting_count: int,
    thresholds: SpeakerCountDriftThresholds = SPEAKER_COUNT_DRIFT_THRESHOLDS,
) -> None:
    """Fail fast when a run's meeting count does not match the frozen speaker-count recipe.

    Speaker-count bands are absolute correct counts out of ``thresholds.n_meetings`` (for example
    7/10). Applying them to a different meeting count would change their meaning silently.
    """
    if run_meeting_count != thresholds.n_meetings:
        msg = (
            "Speaker-count drift check cannot run: meeting count does not match the frozen recipe. "
            f"This evaluation run scored {run_meeting_count} meeting(s), but "
            f"SPEAKER_COUNT_DRIFT_THRESHOLDS is defined for {thresholds.n_meetings} meetings "
            f"(7/10, 6/10, and so on; see larger_cloud_test.yaml num_samples). "
            "Using these thresholds on a different meeting count would mis-classify pass, review, "
            "and fail. Either re-run with the frozen 10-meeting recipe, or update "
            "SPEAKER_COUNT_DRIFT_THRESHOLDS and recompute the speaker-count baseline for the new size."
        )
        raise ValueError(msg)
