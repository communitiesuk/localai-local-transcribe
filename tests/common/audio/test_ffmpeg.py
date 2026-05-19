from pathlib import Path

import pytest

from common.audio.ffmpeg import convert_to_mp3, get_duration, get_num_audio_channels
from tests.utils import FileTypeTests


def _has_audio_data() -> bool:
    path = Path(".data") / "test_audio" / FileTypeTests.NORMAL
    return path.exists() and any(path.iterdir())


@pytest.fixture
def audio_files():
    path = Path(".data") / "test_audio" / FileTypeTests.NORMAL

    if not _has_audio_data():
        pytest.skip(f"Missing test audio data at {path}")

    return list(path.iterdir())


def test_get_duration(audio_files):
    for filename in audio_files:
        result = get_duration(filename)
        assert result > 0


def test_get_num_audio_channels(audio_files):
    for filename in audio_files:
        result = get_num_audio_channels(filename)
        assert result > -1


def test_convert_to_mp3(audio_files):
    for filename in audio_files:
        result = Path(convert_to_mp3(filename))

        assert result.suffix == ".mp3"
        assert result.exists()
        assert result.stat().st_size > 0

        result.unlink()
        assert not result.exists()
