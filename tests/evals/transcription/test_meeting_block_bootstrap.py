"""Tests for corpus WER / WDER and meeting-block bootstrap helpers."""

import pytest

from evals.transcription.src.baseline.bootstrap_common import relative_increase
from evals.transcription.src.baseline.wder_bootstrap import (
    MeetingWderComponents,
    bootstrap_corpus_wder,
    corpus_wder,
)
from evals.transcription.src.baseline.wer_bootstrap import (
    MeetingWerComponents,
    bootstrap_corpus_wer,
    corpus_wer,
)


def _meeting(example_id: str, reference_words: int, errors: int) -> MeetingWerComponents:
    """Build a minimal WER meeting row for unit tests."""
    return MeetingWerComponents(
        example_id=example_id,
        hits=reference_words - errors,
        substitutions=errors,
        deletions=0,
        insertions=0,
        reference_words=reference_words,
        errors=errors,
        meeting_wer=errors / reference_words,
    )


def _wder_meeting(example_id: str, total_words: int, speaker_errors: int) -> MeetingWderComponents:
    """Build a minimal WDER meeting row for unit tests."""
    return MeetingWderComponents(
        example_id=example_id,
        speaker_errors=speaker_errors,
        total_words=total_words,
        meeting_wder=speaker_errors / total_words,
    )


def test_corpus_wer_is_total_errors_over_total_reference_words():
    meetings = [_meeting("0", reference_words=100, errors=10), _meeting("1", reference_words=300, errors=30)]
    assert corpus_wer(meetings) == 40 / 400


def test_bootstrap_corpus_wer_is_deterministic_for_fixed_seed():
    meetings = [_meeting(str(index), reference_words=100 + 10 * index, errors=10 + index) for index in range(5)]
    first = bootstrap_corpus_wer(meetings, n_resamples=200, random_seed=42)
    second = bootstrap_corpus_wer(meetings, n_resamples=200, random_seed=42)
    assert first.tolist() == second.tolist()


def test_corpus_wder_is_total_speaker_errors_over_total_words():
    meetings = [
        _wder_meeting("0", total_words=100, speaker_errors=5),
        _wder_meeting("1", total_words=300, speaker_errors=15),
    ]
    assert corpus_wder(meetings) == 20 / 400


def test_bootstrap_corpus_wder_is_deterministic_for_fixed_seed():
    meetings = [_wder_meeting(str(index), total_words=100 + 10 * index, speaker_errors=5 + index) for index in range(5)]
    first = bootstrap_corpus_wder(meetings, n_resamples=200, random_seed=42)
    second = bootstrap_corpus_wder(meetings, n_resamples=200, random_seed=42)
    assert first.tolist() == second.tolist()


def test_relative_increase():
    assert relative_increase(0.30, 0.25) == pytest.approx(0.20)
