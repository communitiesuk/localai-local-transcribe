"""Tests for corpus WER and meeting-block bootstrap helpers."""

import pytest

from evals.transcription.src.baseline.wer_bootstrap import (
    MeetingWerComponents,
    bootstrap_corpus_wer,
    corpus_wer,
    relative_increase,
)


def _meeting(example_id: str, reference_words: int, errors: int) -> MeetingWerComponents:
    """Build a minimal meeting row for unit tests."""
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


def test_corpus_wer_is_total_errors_over_total_reference_words():
    meetings = [_meeting("0", reference_words=100, errors=10), _meeting("1", reference_words=300, errors=30)]
    assert corpus_wer(meetings) == 40 / 400


def test_bootstrap_corpus_wer_is_deterministic_for_fixed_seed():
    meetings = [_meeting(str(index), reference_words=100 + 10 * index, errors=10 + index) for index in range(5)]
    first = bootstrap_corpus_wer(meetings, n_resamples=200, random_seed=42)
    second = bootstrap_corpus_wer(meetings, n_resamples=200, random_seed=42)
    assert first.tolist() == second.tolist()


def test_relative_increase():
    assert relative_increase(0.30, 0.25) == pytest.approx(0.20)
