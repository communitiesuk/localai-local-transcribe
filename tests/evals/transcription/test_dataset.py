from __future__ import annotations

from unittest.mock import Mock

import numpy as np
import pytest

from evals.transcription.src.core.ami.loader import AMIDatasetSource
from evals.transcription.src.core.dataset import load_benchmark_dataset, prepare_audio_for_transcription
from evals.transcription.src.models import AudioSample, DatasetItem


def test_prepare_audio_for_transcription_uses_cached_path(tmp_path, monkeypatch):
    cached = tmp_path / "cached.wav"
    cached.write_bytes(b"RIFFfake")

    example = DatasetItem(
        audio=AudioSample(path=str(cached), array=np.array([0.0]), sampling_rate=16000),
        text="test",
    )

    mock_ffmpeg = Mock()

    monkeypatch.setattr("ffmpeg.input", mock_ffmpeg)
    monkeypatch.setattr("ffmpeg.output", mock_ffmpeg)
    monkeypatch.setattr("ffmpeg.run", mock_ffmpeg)

    assert prepare_audio_for_transcription(example, 0) == str(cached)

    mock_ffmpeg.assert_not_called()


def test_prepare_audio_for_transcription_downmixes_stereo_and_returns_path(tmp_path, monkeypatch):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    monkeypatch.setattr("evals.transcription.src.core.dataset.AUDIO_DIR", audio_dir)

    samples = np.array([[0.0, 1.0], [1.0, 0.0]])

    captured = {}

    def fake_write(_path, data, _sr, **_kwargs):
        captured["data"] = data

    monkeypatch.setattr("evals.transcription.src.core.audio_cache.soundfile.write", fake_write)
    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", lambda _input, output: output)

    example = DatasetItem(audio=AudioSample(array=samples, sampling_rate=16000, path=""), text="test")
    output_path = prepare_audio_for_transcription(example, 1)

    assert output_path == str(audio_dir / "sample_000001.mp3")
    np.testing.assert_allclose(captured["data"], samples)


def test_prepare_audio_for_transcription_cleans_temp_on_ffmpeg_error(tmp_path, monkeypatch):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    monkeypatch.setattr("evals.transcription.src.core.dataset.AUDIO_DIR", audio_dir)

    temp_path_holder = {}

    def fake_write(path, _data, _sr, **_kwargs):
        temp_path_holder["path"] = path

    def fake_convert_to_mp3_error(_input_path, _output_path):
        msg = "ffmpeg failure"
        raise RuntimeError(msg)

    monkeypatch.setattr("evals.transcription.src.core.audio_cache.soundfile.write", fake_write)
    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", fake_convert_to_mp3_error)

    example = DatasetItem(audio=AudioSample(array=np.zeros((2, 2)), sampling_rate=16000, path=""), text="test")

    with pytest.raises(RuntimeError):
        prepare_audio_for_transcription(example, 2)

    temp_path = temp_path_holder["path"]
    assert temp_path is not None
    assert not temp_path.exists()


def test_load_benchmark_dataset_rejects_unknown_dataset():
    with pytest.raises(ValueError, match="Unknown transcription dataset: nope"):
        load_benchmark_dataset(num_samples=1, dataset_name="nope")


@pytest.mark.parametrize("override", [False, True])
def test_source_resolves_cache_dir_from_default_or_override(tmp_path, monkeypatch, override):
    monkeypatch.setattr("evals.transcription.src.core.benchmark_dataset_source.INPUT_DIR", tmp_path)

    configured_dir = tmp_path / "configured" if override else None
    source = AMIDatasetSource(configured_dir)

    assert source.cache_dir == (configured_dir if override else tmp_path / "ami")


def test_load_benchmark_dataset_builds_from_registered_source(tmp_path, monkeypatch):
    monkeypatch.setattr("evals.transcription.src.core.benchmark_dataset_source.INPUT_DIR", tmp_path)
    loader_class = Mock()
    monkeypatch.setattr("evals.transcription.src.core.ami.loader.AMIDatasetLoader", loader_class)

    load_benchmark_dataset(num_samples=2, dataset_name="ami", sample_duration_fraction=0.5)

    assert loader_class.call_args.args == (tmp_path / "ami", 2, 0.5)
    loader_class.return_value.prepare.assert_called_once()


def test_source_rejects_unsupported_option():
    with pytest.raises(ValueError, match="ami does not support samples_per_group"):
        AMIDatasetSource().load(num_samples=1, samples_per_group=5)


def test_source_accepts_declared_supported_option(tmp_path, monkeypatch):
    monkeypatch.setattr("evals.transcription.src.core.benchmark_dataset_source.INPUT_DIR", tmp_path)
    loader_class = Mock()
    monkeypatch.setattr("evals.transcription.src.core.ami.loader.AMIDatasetLoader", loader_class)

    assert AMIDatasetSource().load(num_samples=1, sample_duration_fraction=0.25) is loader_class.return_value
