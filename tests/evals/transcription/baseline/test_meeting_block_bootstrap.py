"""Tests for corpus WER / WDER and meeting-block bootstrap helpers."""

import json

import pytest

from evals.transcription.src.baseline import compute_bootstrap_artefacts
from evals.transcription.src.baseline.bootstrap_common import relative_increase
from evals.transcription.src.baseline.wder_bootstrap import (
    MeetingWderComponents,
    bootstrap_corpus_wder,
    build_wder_bootstrap_artefact,
    corpus_wder,
    meeting_wder_components_from_sample,
)
from evals.transcription.src.baseline.wer_bootstrap import (
    MeetingWerComponents,
    bootstrap_corpus_wer,
    build_wer_bootstrap_artefact,
    corpus_wer,
    meeting_components_from_sample,
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


@pytest.mark.parametrize(
    "metrics", [{}, {"speaker_errors": None, "total_words": None}, {"speaker_errors": 0, "total_words": 0}]
)
def test_unscorable_wder_sample_returns_no_components(metrics):
    assert meeting_wder_components_from_sample({"example_id": "0", "metrics": metrics}) is None


def test_wder_bootstrap_excludes_unscorable_samples_and_records_them(tmp_path):
    path = tmp_path / "results.json"
    path.write_text(
        json.dumps(
            {
                "engines": {
                    "test": [
                        {"example_id": "missing", "metrics": {}},
                        {"example_id": "empty", "metrics": {"speaker_errors": 0, "total_words": 0}},
                        {"example_id": "valid", "metrics": {"speaker_errors": 2, "total_words": 10}},
                    ]
                }
            }
        )
    )
    artefact = build_wder_bootstrap_artefact(path, n_resamples=20)
    assert artefact is not None
    assert artefact["baseline_corpus_wder"] == pytest.approx(0.2)
    assert artefact["n_meetings"] == 1
    assert artefact["excluded_example_ids"] == ["missing", "empty"]
    assert artefact["bootstrap"]["mean"] == pytest.approx(0.2)


@pytest.mark.parametrize("dataset", ["english_dialects", "audio_files"])
def test_non_diarizing_results_skip_wder_bootstrap_in_cli(tmp_path, monkeypatch, dataset, caplog):
    path = tmp_path / f"{dataset}.json"
    path.write_text(
        json.dumps(
            {
                "engines": {
                    "test": [
                        {
                            "example_id": "0",
                            "metrics": {
                                "hits": 8,
                                "substitutions": 2,
                                "deletions": 0,
                                "insertions": 0,
                            },
                        }
                    ]
                }
            }
        )
    )
    assert build_wder_bootstrap_artefact(path) is None
    monkeypatch.setattr("sys.argv", ["bootstrap", str(path)])
    monkeypatch.setattr(compute_bootstrap_artefacts, "BASELINE_ARTEFACT_DIR", tmp_path)
    wer_path = tmp_path / "wer.json"
    wder_path = tmp_path / "wder.json"
    monkeypatch.setattr(compute_bootstrap_artefacts, "WER_BOOTSTRAP_ARTEFACT_PATH", wer_path)
    monkeypatch.setattr(compute_bootstrap_artefacts, "WDER_BOOTSTRAP_ARTEFACT_PATH", wder_path)
    compute_bootstrap_artefacts.main()
    assert json.loads(wer_path.read_text())["baseline_corpus_wer"] == pytest.approx(0.2)
    assert not wder_path.exists()
    assert "WDER baseline artefact was not updated" in caplog.text


@pytest.mark.parametrize("metrics", [{}, {"hits": 0, "substitutions": 0, "deletions": 0, "insertions": 3}])
def test_unscorable_wer_sample_returns_no_components(metrics):
    assert meeting_components_from_sample({"example_id": "0", "metrics": metrics}) is None


def test_wer_bootstrap_filters_zero_reference_samples(tmp_path):
    path = tmp_path / "results.json"
    path.write_text(
        json.dumps(
            {
                "engines": {
                    "test": [
                        {
                            "example_id": "empty",
                            "metrics": {"hits": 0, "substitutions": 0, "deletions": 0, "insertions": 0},
                        },
                        {
                            "example_id": "valid",
                            "metrics": {"hits": 8, "substitutions": 2, "deletions": 0, "insertions": 0},
                        },
                    ]
                }
            }
        )
    )
    artefact = build_wer_bootstrap_artefact(path, n_resamples=20)
    assert artefact is not None
    assert artefact["baseline_corpus_wer"] == pytest.approx(0.2)
    assert artefact["excluded_example_ids"] == ["empty"]


def test_cli_continues_to_wder_when_wer_is_unscorable(tmp_path, monkeypatch, caplog):
    path = tmp_path / "results.json"
    path.write_text(
        json.dumps(
            {
                "engines": {
                    "test": [
                        {
                            "example_id": "0",
                            "metrics": {
                                "hits": 0,
                                "substitutions": 0,
                                "deletions": 0,
                                "insertions": 0,
                                "speaker_errors": 2,
                                "total_words": 10,
                            },
                        }
                    ]
                }
            }
        )
    )
    monkeypatch.setattr("sys.argv", ["bootstrap", str(path)])
    monkeypatch.setattr(compute_bootstrap_artefacts, "BASELINE_ARTEFACT_DIR", tmp_path)
    wer_path, wder_path = tmp_path / "wer.json", tmp_path / "wder.json"
    monkeypatch.setattr(compute_bootstrap_artefacts, "WER_BOOTSTRAP_ARTEFACT_PATH", wer_path)
    monkeypatch.setattr(compute_bootstrap_artefacts, "WDER_BOOTSTRAP_ARTEFACT_PATH", wder_path)
    compute_bootstrap_artefacts.main()
    assert not wer_path.exists()
    assert json.loads(wder_path.read_text())["baseline_corpus_wder"] == pytest.approx(0.2)
    assert "WER baseline artefact was not updated" in caplog.text
