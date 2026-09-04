from __future__ import annotations

import json

import pytest

from evals.transcription.src.core.audio_files_dataset import load_audio_files_dataset


def test_load_audio_files_dataset_reads_audio_with_txt_sidecar(tmp_path):
    audio = tmp_path / "sample.mp3"
    audio.write_bytes(b"audio")
    audio.with_suffix(".txt").write_text("hello world", encoding="utf-8")

    dataset = load_audio_files_dataset(tmp_path)

    assert len(dataset) == 1
    sample = dataset[0]
    assert sample.audio.path == str(audio)
    assert sample.text == "hello world"
    assert sample.reference_diarization == [
        {"speaker": "Speaker 1", "text": "hello world", "start_time": 0.0, "end_time": 0.0}
    ]
    assert dataset.dataset_version == "audio_files_v0"
    assert dataset.dataset_split == "n1"


def test_load_audio_files_dataset_reads_ref_diarization(tmp_path):
    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"audio")
    audio.with_suffix(".txt").write_text("hello world", encoding="utf-8")
    diarization = [{"speaker": "A", "text": "hello", "start_time": 0.0, "end_time": 1.0}]
    audio.with_name("sample_ref_diarization.json").write_text(json.dumps(diarization), encoding="utf-8")

    dataset = load_audio_files_dataset(tmp_path)

    assert dataset[0].reference_diarization == diarization


def test_load_audio_files_dataset_requires_txt_sidecar(tmp_path):
    (tmp_path / "sample.mp3").write_bytes(b"audio")

    with pytest.raises(FileNotFoundError, match="Missing reference transcript"):
        load_audio_files_dataset(tmp_path)
