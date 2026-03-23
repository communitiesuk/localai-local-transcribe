from pathlib import Path

from evals.audio_generation.src.utils.parsing_utils import save_audio


def test_save_audio(tmp_path):
    audio_bytes = b"test audio data"
    output_file = "output.mp3"

    saved_path = save_audio(audio_bytes, output_file, target_dir=tmp_path)
    saved_path = Path(saved_path)

    assert saved_path.parent == tmp_path
    assert saved_path.suffix == ".mp3"
    assert saved_path.stem.startswith("output_")

    assert saved_path.read_bytes() == audio_bytes
