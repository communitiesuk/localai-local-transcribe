"""Tests for transcription drift threshold helpers (AIILG-680)."""

import json

import pytest

from evals.transcription.src.constants import (
    PROCESSING_SPEED_DRIFT_THRESHOLDS,
    SPEAKER_COUNT_DRIFT_THRESHOLDS,
    WER_DRIFT_THRESHOLDS,
)
from evals.transcription.src.drift import (
    apply_drift_thresholds,
    classify_processing_speed_drift,
    classify_speaker_count_drift,
    classify_wer_drift,
    require_meeting_count_matches_eval_config,
    worst_outcome,
)
from evals.transcription.src.models import AggregatedMetricStats, EngineOutput, SampleRow, Summary


def test_require_meeting_count_matches_eval_config_accepts_matching_count():
    require_meeting_count_matches_eval_config(SPEAKER_COUNT_DRIFT_THRESHOLDS.n_meetings)


def test_require_meeting_count_matches_eval_config_rejects_mismatch():
    with pytest.raises(ValueError, match="meeting count does not match the baseline transcription eval config"):
        require_meeting_count_matches_eval_config(8)


def test_classify_wer_pass_within_bounds():
    verdict = classify_wer_drift(WER_DRIFT_THRESHOLDS.baseline_corpus_wer)
    assert verdict.outcome == "pass"


def test_classify_wer_review_breach():
    observed = WER_DRIFT_THRESHOLDS.baseline_corpus_wer * (1 + WER_DRIFT_THRESHOLDS.review_relative_increase + 0.01)
    verdict = classify_wer_drift(observed)
    assert verdict.outcome == "review"


def test_classify_wer_fail_breach():
    # Sit clearly above the fail band so float rounding cannot land in review.
    observed = WER_DRIFT_THRESHOLDS.baseline_corpus_wer * (1 + WER_DRIFT_THRESHOLDS.fail_relative_increase + 0.01)
    verdict = classify_wer_drift(observed)
    assert verdict.outcome == "fail"


def test_classify_wer_absolute_floor_breach():
    verdict = classify_wer_drift(WER_DRIFT_THRESHOLDS.absolute_floor)
    assert verdict.outcome == "floor"


def test_classify_speaker_count_four_cases():
    n_meetings = SPEAKER_COUNT_DRIFT_THRESHOLDS.n_meetings
    assert classify_speaker_count_drift(7, n_meetings).outcome == "pass"
    assert classify_speaker_count_drift(6, n_meetings).outcome == "review"
    assert classify_speaker_count_drift(5, n_meetings).outcome == "fail"
    assert classify_speaker_count_drift(4, n_meetings).outcome == "floor"


def test_classify_processing_speed_four_cases():
    baseline = PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio
    assert classify_processing_speed_drift(baseline).outcome == "pass"
    assert (
        classify_processing_speed_drift(
            baseline * (1 + PROCESSING_SPEED_DRIFT_THRESHOLDS.review_relative_increase + 0.01)
        ).outcome
        == "review"
    )
    assert (
        classify_processing_speed_drift(
            baseline * (1 + PROCESSING_SPEED_DRIFT_THRESHOLDS.fail_relative_increase + 0.01)
        ).outcome
        == "fail"
    )
    assert classify_processing_speed_drift(PROCESSING_SPEED_DRIFT_THRESHOLDS.absolute_floor).outcome == "floor"


def test_worst_outcome_orders_severity():
    assert worst_outcome(["pass", "review"]) == "review"
    assert worst_outcome(["review", "fail"]) == "fail"
    assert worst_outcome(["fail", "floor"]) == "floor"


def _sample_row(
    example_id: str,
    *,
    speaker_count_accuracy: float,
    hits: int,
    substitutions: int,
    deletions: int,
    insertions: int,
) -> SampleRow:
    """Build a minimal sample row for drift apply tests."""
    return SampleRow(
        run_id="run",
        timestamp="ts",
        example_id=example_id,
        engine_version="azure_stt_synchronous",
        reference_transcript="ref",
        reference_dialogue_entries=None,
        hypothesis_transcript="hyp",
        hypothesis_dialogue_entries=None,
        latency_ms=1.0,
        metrics={
            "wer": 0.0,
            "hits": float(hits),
            "substitutions": float(substitutions),
            "deletions": float(deletions),
            "insertions": float(insertions),
            "wder": 0.0,
            "speaker_errors": 0.0,
            "total_words": float(hits + substitutions + deletions),
            "speaker_count_accuracy": speaker_count_accuracy,
            "ref_speaker_count": 2.0,
            "hyp_speaker_count": 2.0,
            "processing_speed_ratio": 0.04,
        },
    )


def _engine_output(samples: list[SampleRow], processing_speed_ratio: float) -> EngineOutput:
    """Build a minimal engine output for drift apply tests."""
    return EngineOutput(
        summary=Summary(
            run_id="run",
            timestamp="ts",
            dataset_version="AMI_v0",
            engine_version="azure_stt_synchronous",
            split="test",
            n_examples=len(samples),
            metrics={"wer": AggregatedMetricStats(mean=0.0, std=0.0, min=0.0, max=0.0)},
            processing_speed_ratio=processing_speed_ratio,
        ),
        samples=samples,
    )


def _meetings_at_corpus_wer(target_corpus_wer: float, correct_speaker_meetings: int) -> list[SampleRow]:
    """Build ten meetings whose corpus WER equals ``target_corpus_wer``."""
    reference_words_per_meeting = 1_000
    errors_per_meeting = int(round(target_corpus_wer * reference_words_per_meeting))
    hits = reference_words_per_meeting - errors_per_meeting
    samples: list[SampleRow] = []
    for index in range(SPEAKER_COUNT_DRIFT_THRESHOLDS.n_meetings):
        speaker_accuracy = 1.0 if index < correct_speaker_meetings else 0.0
        samples.append(
            _sample_row(
                str(index),
                speaker_count_accuracy=speaker_accuracy,
                hits=hits,
                substitutions=errors_per_meeting,
                deletions=0,
                insertions=0,
            )
        )
    return samples


def test_apply_drift_thresholds_writes_review_file_and_exits_zero(tmp_path):
    # Corpus WER just above the review band; speaker count and speed stay at pass.
    review_corpus_wer = WER_DRIFT_THRESHOLDS.baseline_corpus_wer * (
        1 + WER_DRIFT_THRESHOLDS.review_relative_increase + 0.01
    )
    samples = _meetings_at_corpus_wer(
        review_corpus_wer,
        correct_speaker_meetings=SPEAKER_COUNT_DRIFT_THRESHOLDS.baseline_correct_count,
    )
    engine = _engine_output(samples, PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio)

    exit_code = apply_drift_thresholds([engine], tmp_path, "20260101_000000")
    assert exit_code == 0
    review_path = tmp_path / "drift_review_20260101_000000.json"
    assert review_path.exists()
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    assert payload["overall_outcome"] == "review"


def test_apply_drift_thresholds_exits_one_on_floor(tmp_path):
    samples = _meetings_at_corpus_wer(
        WER_DRIFT_THRESHOLDS.baseline_corpus_wer,
        correct_speaker_meetings=0,
    )
    engine = _engine_output(samples, PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio)
    assert apply_drift_thresholds([engine], tmp_path, "20260101_000001") == 1
    assert not (tmp_path / "drift_review_20260101_000001.json").exists()
