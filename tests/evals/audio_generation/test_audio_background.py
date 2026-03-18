import pytest

from evals.audio_generation.audio_transformation import audio_background


def test_mp3_to_bytes_reads_file(tmp_path, monkeypatch):
    audio_gen_root = tmp_path
    subdir = audio_gen_root / "background_sfx"
    subdir.mkdir()

    fake_file = subdir / "noise.mp3"
    fake_bytes = b"fake mp3 content"
    fake_file.write_bytes(fake_bytes)

    monkeypatch.setattr(
        audio_background,
        "__file__",
        str(tmp_path / "audio_background" / "dummy.py"),
    )

    name, content = audio_background.mp3_to_bytes("background_sfx/noise.mp3")

    assert name == "noise"
    assert content == fake_bytes


def test_mp3_to_bytes_raises_if_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        audio_background,
        "__file__",
        str(tmp_path / "audio_background" / "dummy.py"),
    )

    with pytest.raises(FileNotFoundError):
        audio_background.mp3_to_bytes("does_not_exist.mp3")
