from pathlib import Path

import pytest

from common.audio.ffmpeg import convert_to_mp3, get_duration, get_num_audio_channels
from tests.utils import FileTypeTests


def get_normal_data() -> list[Path]:
    path = Path(".data") / "test_audio" / FileTypeTests.NORMAL

    if not path.exists() or not any(path.iterdir()):
        pytest.skip(
            f"Missing test audio data at {path}",
            allow_module_level=True,
        )

    return list(path.iterdir())


@pytest.mark.parametrize("filename", get_normal_data())
def test_get_duration(filename: Path):
    result = get_duration(filename)
    assert result > 0


@pytest.mark.parametrize("filename", get_normal_data())
def test_get_num_audio_channels(filename: Path):
    result = get_num_audio_channels(filename)
    assert result > -1


@pytest.mark.parametrize("filename", get_normal_data())
def test_convert_to_mp3(filename: Path):
    result = Path(convert_to_mp3(filename))

    assert result.suffix == ".mp3"
    assert result.exists()
    assert result.stat().st_size > 0

    result.unlink()
    assert not result.exists()
