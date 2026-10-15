from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest
import soundfile
import soundfile as sf

from evals.transcription.src.core.audio_cache import AudioFileHandler


def test_audio_cache_read_returns_numpy_array(tmp_path):
    audio_path = tmp_path / "test.wav"
    expected_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    sf.write(audio_path, expected_audio, 16000)

    loaded_audio, sample_rate = AudioFileHandler().read(audio_path)

    assert sample_rate == 16000
    assert isinstance(loaded_audio, np.ndarray)
    assert len(loaded_audio) == len(expected_audio)
    np.testing.assert_allclose(loaded_audio, expected_audio, rtol=1e-3, atol=1e-4)


def test_audio_cache_write_creates_mp3_file(tmp_path, monkeypatch):
    audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    output_path = tmp_path / "output.mp3"

    def fake_convert(_input_path, output_path):
        output_path.write_bytes(b"fake mp3 data")

    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", fake_convert)

    AudioFileHandler().write(output_path, audio_data, 16000)

    assert output_path.exists()


def test_audio_cache_contains_reports_presence(tmp_path):
    cached = tmp_path / "present.mp3"
    cached.write_bytes(b"fake mp3 data")

    assert AudioFileHandler().contains(cached)
    assert not AudioFileHandler().contains(tmp_path / "absent.mp3")


def test_audio_write_cleans_temporary_wav_when_soundfile_write_fails(tmp_path, monkeypatch):
    temporary_paths = []

    def fail_write(path, *_args, **_kwargs):
        temporary_paths.append(path)
        message = "write failed"
        raise OSError(message)

    monkeypatch.setattr("evals.transcription.src.core.audio_cache.soundfile.write", fail_write)
    with pytest.raises(OSError, match="write failed"):
        AudioFileHandler().write(tmp_path / "sample.mp3", np.zeros(160), 16000)
    assert len(temporary_paths) == 1
    assert not temporary_paths[0].exists()


def test_audio_read_uses_native_path_io_after_preflight(tmp_path):
    audio_path = tmp_path / "audio.wav"
    soundfile.write(audio_path, np.zeros(160), 16000)
    with patch("evals.transcription.src.core.audio_cache.soundfile.read", wraps=soundfile.read) as read:
        loaded, sample_rate = AudioFileHandler().read(audio_path)
    read.assert_called_once_with(audio_path)
    assert len(loaded) == 160
    assert sample_rate == 16000


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt])
def test_failed_encode_does_not_publish_partial_mp3(tmp_path, monkeypatch, existing, error_type):
    destination = tmp_path / "sample.mp3"
    if existing:
        destination.write_bytes(b"previous complete audio")
    temporary_paths = []

    def interrupted_encode(source, target):
        temporary_paths.extend([source, target])
        assert target.parent == destination.parent
        assert target.suffix == ".mp3"
        target.write_bytes(b"partial mp3")
        if existing:
            assert destination.read_bytes() == b"previous complete audio"
        else:
            assert not destination.exists()
        message = "encode interrupted"
        raise error_type(message)

    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", interrupted_encode)
    with pytest.raises(error_type, match="encode interrupted"):
        AudioFileHandler().write(destination, np.zeros(160), 16000)
    if existing:
        assert destination.read_bytes() == b"previous complete audio"
    else:
        assert not destination.exists()
    assert all(not path.exists() for path in temporary_paths)


def test_successful_encode_publishes_only_after_completion(tmp_path, monkeypatch):
    destination = tmp_path / "sample.mp3"
    destination.write_bytes(b"previous complete audio")
    temporary_paths = []

    def encode(source, target):
        temporary_paths.extend([source, target])
        target.write_bytes(b"new complete audio")
        assert destination.read_bytes() == b"previous complete audio"

    monkeypatch.setattr("evals.transcription.src.core.audio_cache.convert_to_mp3", encode)
    AudioFileHandler().write(destination, np.zeros(160), 16000)
    assert destination.read_bytes() == b"new complete audio"
    assert all(not path.exists() for path in temporary_paths)
