"""Tests for transcription drift threshold helpers."""

import pytest

from evals.transcription.src.constants import SPEAKER_COUNT_DRIFT_THRESHOLDS
from evals.transcription.src.drift import require_speaker_count_recipe_size


def test_require_speaker_count_recipe_size_accepts_matching_count():
    require_speaker_count_recipe_size(SPEAKER_COUNT_DRIFT_THRESHOLDS.n_meetings)


def test_require_speaker_count_recipe_size_rejects_mismatch():
    with pytest.raises(ValueError, match="meeting count does not match the frozen recipe"):
        require_speaker_count_recipe_size(8)
