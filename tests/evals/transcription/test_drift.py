"""Tests for transcription drift threshold helpers (AIILG-680)."""

import json

import pytest

from evals.transcription.src.constants import (
    PROCESSING_SPEED_DRIFT_THRESHOLDS,
    SPEAKER_COUNT_DRIFT_THRESHOLDS,
    WDER_DRIFT_THRESHOLDS,
    WER_DRIFT_THRESHOLDS,
)
from evals.transcription.src.drift import (
    apply_drift_thresholds,
    assess_engine_drift,
    classify_processing_speed_drift,
    classify_speaker_count_drift,
    classify_wder_drift,
    classify_wer_drift,
    corpus_wder_from_samples,
    corpus_wer_from_samples,
    is_wer_scorable,
    require_meeting_count_matches_eval_config,
    speaker_correct_count,
    worst_outcome,
)
from evals.transcription.src.models import AggregatedMetricStats, EngineOutput, SampleRow, Summary


def test_require_meeting_count_matches_eval_config_accepts_matching_count():
    require_meeting_count_matches_eval_config(SPEAKER_COUNT_DRIFT_THRESHOLDS.n_meetings)


def test_require_meeting_count_matches_eval_config_rejects_mismatch():
    with pytest.raises(ValueError, match="Meeting count does not match the baseline transcription eval config"):
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


def test_classify_wder_pass_within_bounds():
    verdict = classify_wder_drift(WDER_DRIFT_THRESHOLDS.baseline_corpus_wder)
    assert verdict.outcome == "pass"


def test_classify_wder_review_breach():
    observed = WDER_DRIFT_THRESHOLDS.baseline_corpus_wder * (1 + WDER_DRIFT_THRESHOLDS.review_relative_increase + 0.01)
    verdict = classify_wder_drift(observed)
    assert verdict.outcome == "review"


def test_classify_wder_fail_breach():
    # Sit clearly above the fail band so float rounding cannot land in review.
    observed = WDER_DRIFT_THRESHOLDS.baseline_corpus_wder * (1 + WDER_DRIFT_THRESHOLDS.fail_relative_increase + 0.01)
    verdict = classify_wder_drift(observed)
    assert verdict.outcome == "fail"


def test_classify_wder_absolute_floor_breach():
    verdict = classify_wder_drift(WDER_DRIFT_THRESHOLDS.absolute_floor)
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


def test_worst_outcome_rejects_empty_list():
    with pytest.raises(ValueError, match="worst_outcome requires at least one drift outcome"):
        worst_outcome([])


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
            "reference_speaker_count": 2.0,
            "predicted_speaker_count": 2.0,
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
    errors_per_meeting = round(target_corpus_wer * reference_words_per_meeting)
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
    # Corpus WER just above the review band; WDER, speaker count, and speed stay at pass.
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
    exit_code = apply_drift_thresholds([engine], tmp_path, "20260101_000001")
    assert exit_code == 1
    review_path = tmp_path / "drift_review_20260101_000001.json"
    assert review_path.exists()
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    assert payload["overall_outcome"] == "floor"


@pytest.mark.parametrize("omit_metrics", [False, True])
def test_drift_skips_unavailable_diarization_metrics(tmp_path, omit_metrics):
    samples = _meetings_at_corpus_wer(
        WER_DRIFT_THRESHOLDS.baseline_corpus_wer,
        correct_speaker_meetings=SPEAKER_COUNT_DRIFT_THRESHOLDS.baseline_correct_count,
    )
    for sample in samples:
        for key in ("wder", "speaker_errors", "total_words", "speaker_count_accuracy"):
            if omit_metrics:
                sample.metrics.pop(key)
            else:
                sample.metrics[key] = None
    engine = _engine_output(samples, PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio)
    assert corpus_wder_from_samples(samples) is None
    assert speaker_correct_count(samples) == 0
    verdicts = assess_engine_drift(engine, supports_diarization=False)
    assert len(verdicts) == 4
    assert sum(verdict.outcome == "review" for verdict in verdicts) == 2
    assert (
        apply_drift_thresholds(
            [engine], tmp_path, "non_diarizing", diarization_capabilities={engine.summary.engine_version: False}
        )
        == 0
    )
    payload = json.loads((tmp_path / "drift_review_non_diarizing.json").read_text())
    assert payload["overall_outcome"] == "review"
    skipped = [check for check in payload["checks"] if check["outcome"] == "review"]
    assert len(skipped) == 2
    assert all(check["observed"] is None for check in skipped)
    if not omit_metrics:
        assert engine.samples[0].model_dump()["metrics"]["wder"] is None


def test_zero_word_sample_does_not_disable_wder_failure(tmp_path):
    samples = _meetings_at_corpus_wer(
        WER_DRIFT_THRESHOLDS.baseline_corpus_wer,
        correct_speaker_meetings=SPEAKER_COUNT_DRIFT_THRESHOLDS.baseline_correct_count,
    )
    samples[0].metrics.update(speaker_errors=0, total_words=0)
    for sample in samples[1:]:
        sample.metrics.update(speaker_errors=1000, total_words=1000)
    engine = _engine_output(samples, PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio)
    assert corpus_wder_from_samples(samples) == 1.0
    assert apply_drift_thresholds([engine], tmp_path, "zero_words") == 1
    payload = json.loads((tmp_path / "drift_review_zero_words.json").read_text())
    wder = next(check for check in payload["checks"] if check["metric"] == "corpus_wder")
    assert wder["outcome"] in {"fail", "floor"}
    assert "Excluded 1" in wder["detail"]


def test_unscorable_diarizing_run_creates_review_artifact(tmp_path):
    samples = _meetings_at_corpus_wer(
        WER_DRIFT_THRESHOLDS.baseline_corpus_wer,
        correct_speaker_meetings=SPEAKER_COUNT_DRIFT_THRESHOLDS.baseline_correct_count,
    )
    for sample in samples:
        sample.metrics.update(speaker_errors=0, total_words=0)
    engine = _engine_output(samples, PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio)
    assert corpus_wder_from_samples(samples) is None
    assert apply_drift_thresholds([engine], tmp_path, "unscorable") == 0
    payload = json.loads((tmp_path / "drift_review_unscorable.json").read_text())
    wder = next(check for check in payload["checks"] if check["metric"] == "corpus_wder")
    assert wder["outcome"] == "review"
    assert wder["observed"] is None


def test_zero_reference_word_sample_is_excluded_from_corpus_wer(tmp_path):
    samples = _meetings_at_corpus_wer(
        WER_DRIFT_THRESHOLDS.baseline_corpus_wer,
        correct_speaker_meetings=SPEAKER_COUNT_DRIFT_THRESHOLDS.baseline_correct_count,
    )

    samples[0].metrics.update(hits=0.0, substitutions=0.0, deletions=0.0, insertions=0.0, total_words=1_000.0)

    assert not is_wer_scorable(samples[0])
    assert corpus_wer_from_samples(samples) == pytest.approx(corpus_wer_from_samples(samples[1:]))

    engine = _engine_output(samples, PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio)
    assert apply_drift_thresholds([engine], tmp_path, "wer_excluded") == 0
    payload = json.loads((tmp_path / "drift_review_wer_excluded.json").read_text())
    wer = next(check for check in payload["checks"] if check["metric"] == "corpus_wer")
    assert wer["outcome"] == "review"
    assert "Excluded 1" in wer["detail"]


def test_corpus_wer_without_scorable_samples_reports_review(tmp_path):
    samples = _meetings_at_corpus_wer(
        WER_DRIFT_THRESHOLDS.baseline_corpus_wer,
        correct_speaker_meetings=SPEAKER_COUNT_DRIFT_THRESHOLDS.baseline_correct_count,
    )
    for sample in samples:
        sample.metrics.update(hits=0.0, substitutions=0.0, deletions=0.0, insertions=0.0, total_words=1_000.0)

    assert corpus_wer_from_samples(samples) is None

    engine = _engine_output(samples, PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio)
    assert apply_drift_thresholds([engine], tmp_path, "wer_unscorable") == 0
    payload = json.loads((tmp_path / "drift_review_wer_unscorable.json").read_text())
    wer = next(check for check in payload["checks"] if check["metric"] == "corpus_wer")
    assert wer["outcome"] == "review"
    assert wer["observed"] is None
