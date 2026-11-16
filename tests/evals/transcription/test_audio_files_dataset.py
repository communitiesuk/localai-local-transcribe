from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile

from evals.transcription.src.core.audio_files_dataset import AudioFilesDataset


def test_audio_files_dataset_reads_audio_with_txt_sidecar(tmp_path):
    audio = tmp_path / "sample.wav"
    soundfile.write(audio, np.zeros(100), 16000)
    audio.with_suffix(".txt").write_text("hello world", encoding="utf-8")

    dataset = AudioFilesDataset(tmp_path)

    assert len(dataset) == 1
    sample = dataset[0]
    assert sample.audio.path == str(audio)
    assert sample.text == "hello world"
    assert sample.reference_diarization == []
    assert not dataset.supports_diarization


def test_audio_files_dataset_reads_ref_diarization(tmp_path):
    audio = tmp_path / "sample.wav"
    soundfile.write(audio, np.zeros(100), 16000)
    audio.with_suffix(".txt").write_text("hello world", encoding="utf-8")
    diarization = [{"speaker": "A", "text": "hello", "start_time": 0.0, "end_time": 1.0}]
    audio.with_name("sample_ref_diarization.json").write_text(json.dumps(diarization), encoding="utf-8")

    dataset = AudioFilesDataset(tmp_path)

    assert dataset[0].reference_diarization == diarization
    assert dataset.supports_diarization


def test_audio_files_dataset_requires_txt_sidecar(tmp_path):
    (tmp_path / "sample.mp3").write_bytes(b"audio")

    with pytest.raises(FileNotFoundError, match="Missing reference transcript"):
        AudioFilesDataset(tmp_path)
