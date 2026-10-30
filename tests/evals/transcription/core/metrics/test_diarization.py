from __future__ import annotations

import jiwer
import pytest

from evals.transcription.src.core.metrics import compute_speaker_count_metrics, compute_wder
from evals.transcription.src.core.metrics.diarization import find_optimal_speaker_mapping


@pytest.mark.parametrize(
    ("ref_segments", "hyp_segments", "expected"),
    [
        (
            [
                {"speaker": "Speaker_1", "text": "hello world", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_2", "text": "good morning", "start": 1.0, "end": 2.0},
            ],
            [
                {"speaker": "Speaker_A", "text": "hello world", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_B", "text": "good morning", "start": 1.0, "end": 2.0},
            ],
            {"wder": 0.0, "speaker_errors": 0, "total_words": 4},
        ),
        ([], [], {"wder": 0.0, "speaker_errors": 0, "total_words": 0}),
        (
            [{"speaker": "Speaker_1", "text": "hello world", "start": 0.0, "end": 1.0}],
            [],
            {"wder": 0.0, "speaker_errors": 0, "total_words": 2},
        ),
        (
            [
                {"speaker": "Speaker_1", "text": "hello world", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_2", "text": "good morning", "start": 1.0, "end": 2.0},
                {"speaker": "Speaker_3", "text": "goodbye", "start": 2.0, "end": 2.5},
            ],
            [
                {"speaker": "Speaker_A", "text": "hello world", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_B", "text": "good morning goodbye", "start": 1.0, "end": 2.5},
            ],
            {"wder": 0.2, "speaker_errors": 1, "total_words": 5},
        ),
        (
            [{"speaker": "Speaker_1", "text": "hello world", "start": 0.0, "end": 1.0}],
            [
                {"speaker": "Speaker_A", "text": "hello world", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_B", "text": "extra words", "start": 1.0, "end": 1.5},
            ],
            {"wder": 0.0, "speaker_errors": 0, "total_words": 2},
        ),
        (
            [
                {"speaker": "Speaker_1", "text": "hello world", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_2", "text": "good morning", "start": 1.0, "end": 2.0},
            ],
            [
                {"speaker": "Speaker_2", "text": "hello world", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_1", "text": "good morning", "start": 1.0, "end": 2.0},
            ],
            {"wder": 0.0, "speaker_errors": 0, "total_words": 4},
        ),
        (
            [
                {"speaker": "Speaker_1", "text": "hello world", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_2", "text": "good morning", "start": 1.0, "end": 2.0},
                {"speaker": "Speaker_1", "text": "goodbye", "start": 2.0, "end": 2.5},
            ],
            [
                {"speaker": "Speaker_A", "text": "hello world", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_B", "text": "good morning", "start": 1.0, "end": 2.0},
                {"speaker": "Speaker_B", "text": "goodbye", "start": 2.0, "end": 2.5},
            ],
            {"wder": 0.2, "speaker_errors": 1, "total_words": 5},
        ),
        (
            [{"speaker": "Speaker_1", "text": "Hello, World!", "start": 0.0, "end": 1.0}],
            [{"speaker": "Speaker_A", "text": "hello world", "start": 0.0, "end": 1.0}],
            {"wder": 0.0, "speaker_errors": 0, "total_words": 2},
        ),
        (
            [
                {"speaker": "Speaker_1", "text": "one two three", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_2", "text": "four five six", "start": 1.0, "end": 2.0},
                {"speaker": "Speaker_3", "text": "seven eight nine", "start": 2.0, "end": 3.0},
            ],
            [
                {"speaker": "Speaker_C", "text": "one two three", "start": 0.0, "end": 1.0},
                {"speaker": "Speaker_A", "text": "four five six", "start": 1.0, "end": 2.0},
                {"speaker": "Speaker_B", "text": "seven eight nine", "start": 2.0, "end": 3.0},
            ],
            {"wder": 0.0, "speaker_errors": 0, "total_words": 9},
        ),
        (
            [{"speaker": "Speaker_1", "text": "hello world test", "start": 0.0, "end": 1.0}],
            [{"speaker": "Speaker_A", "text": "hello world", "start": 0.0, "end": 1.0}],
            {"wder": 0.0, "speaker_errors": 0, "total_words": 3},
        ),
    ],
)
def test_compute_wder(ref_segments, hyp_segments, expected):
    result = compute_wder(ref_segments, hyp_segments)
    assert result == expected


def test_compute_wder_orders_segments_chronologically():
    reference = [
        {"speaker": "Speaker_2", "text": "good morning", "start": 1.0, "end": 2.0},
        {"speaker": "Speaker_1", "text": "hello world", "start": 0.0, "end": 1.0},
    ]
    hypothesis = [
        {"speaker": "Speaker_A", "text": "hello world", "start": 0.0, "end": 1.0},
        {"speaker": "Speaker_B", "text": "good morning", "start": 1.0, "end": 2.0},
    ]

    assert compute_wder(reference, hypothesis) == {
        "wder": 0.0,
        "speaker_errors": 0,
        "total_words": 4,
    }


@pytest.mark.parametrize(
    ("ref_segments", "hyp_segments", "expected"),
    [
        (
            [
                {"speaker": "Speaker_1", "text": "hello", "start": 0.0, "end": 0.5},
                {"speaker": "Speaker_2", "text": "world", "start": 0.5, "end": 1.0},
            ],
            [
                {"speaker": "Speaker_A", "text": "hello", "start": 0.0, "end": 0.5},
                {"speaker": "Speaker_B", "text": "world", "start": 0.5, "end": 1.0},
            ],
            {"speaker_count_accuracy": 1.0, "ref_speaker_count": 2, "hyp_speaker_count": 2, "absolute_error": 0},
        ),
        (
            [
                {"speaker": "Speaker_1", "text": "hello", "start": 0.0, "end": 0.5},
                {"speaker": "Speaker_2", "text": "world", "start": 0.5, "end": 1.0},
            ],
            [{"speaker": "Speaker_A", "text": "hello world", "start": 0.0, "end": 1.0}],
            {"speaker_count_accuracy": 0.0, "ref_speaker_count": 2, "hyp_speaker_count": 1, "absolute_error": 1},
        ),
        (
            [],
            [],
            {"speaker_count_accuracy": 1.0, "ref_speaker_count": 0, "hyp_speaker_count": 0, "absolute_error": 0},
        ),
        (
            [{"speaker": "Speaker_1", "text": "hello", "start": 0.0, "end": 0.5}],
            [
                {"speaker": "Speaker_A", "text": "hello", "start": 0.0, "end": 0.5},
                {"speaker": "Speaker_B", "text": "world", "start": 0.5, "end": 1.0},
            ],
            {"speaker_count_accuracy": 0.0, "ref_speaker_count": 1, "hyp_speaker_count": 2, "absolute_error": 1},
        ),
        (
            [
                {"speaker": "Speaker_1", "text": "hello", "start": 0.0, "end": 0.5},
                {"speaker": "Speaker_2", "text": "world", "start": 0.5, "end": 1.0},
                {"speaker": "Speaker_3", "text": "test", "start": 1.0, "end": 1.5},
            ],
            [{"speaker": "Speaker_A", "text": "hello world test", "start": 0.0, "end": 1.5}],
            {"speaker_count_accuracy": 0.0, "ref_speaker_count": 3, "hyp_speaker_count": 1, "absolute_error": 2},
        ),
        (
            [
                {"speaker": "Speaker_1", "text": "hello", "start": 0.0, "end": 0.5},
                {"speaker": "Speaker_1", "text": "world", "start": 0.5, "end": 1.0},
                {"speaker": "Speaker_2", "text": "test", "start": 1.0, "end": 1.5},
            ],
            [
                {"speaker": "Speaker_A", "text": "hello", "start": 0.0, "end": 0.5},
                {"speaker": "Speaker_A", "text": "world", "start": 0.5, "end": 1.0},
                {"speaker": "Speaker_B", "text": "test", "start": 1.0, "end": 1.5},
            ],
            {"speaker_count_accuracy": 1.0, "ref_speaker_count": 2, "hyp_speaker_count": 2, "absolute_error": 0},
        ),
    ],
)
def test_compute_speaker_count_metrics(ref_segments, hyp_segments, expected):
    result = compute_speaker_count_metrics(ref_segments, hyp_segments)
    assert result == expected


def test_speaker_mapping_maximises_total_overlap_rather_than_greedy_matches():
    # X overlaps A on 5 words and B on 4; Y overlaps A on 4.
    # Choosing X->A greedily yields 5 matches; X->B and Y->A yields 8.
    reference_speakers = ["A"] * 5 + ["B"] * 4 + ["A"] * 4
    hypothesis_speakers = ["X"] * 9 + ["Y"] * 4
    words = [f"word{index}" for index in range(13)]
    alignment = jiwer.process_words(" ".join(words), " ".join(words))

    mapping = find_optimal_speaker_mapping(
        list(zip(words, reference_speakers, strict=True)),
        list(zip(words, hypothesis_speakers, strict=True)),
        alignment,
    )

    assert mapping == {"X": "B", "Y": "A"}


def test_speaker_mapping_does_not_accept_zero_overlap_assignment():
    reference = [("hello", "A"), ("there", "B")]
    hypothesis = [("hello", "X"), ("different", "Y")]
    alignment = jiwer.process_words("hello there", "hello different")

    assert find_optimal_speaker_mapping(reference, hypothesis, alignment) == {"X": "A", "Y": "UNMAPPED_Y"}


def test_speaker_mapping_leaves_extra_hypothesis_speakers_unmapped():
    reference = [("one", "A"), ("two", "A"), ("three", "A")]
    hypothesis = [("one", "X"), ("two", "X"), ("three", "Y")]
    alignment = jiwer.process_words("one two three", "one two three")

    assert find_optimal_speaker_mapping(reference, hypothesis, alignment) == {"X": "A", "Y": "UNMAPPED_Y"}
