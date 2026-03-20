from pathlib import Path

from evals.audio_generation.src.utils.parsing_utils import build_pattern, extract_speakers, save_audio


def test_build_pattern():
    speakers = ["Alice", "Bob"]
    pattern = build_pattern(speakers)
    assert pattern == r"(Alice|Bob):\s*(.+?)(?=(Alice|Bob):|$)"


def test_save_audio(tmp_path):
    audio_bytes = b"test audio data"
    output_file = "output.mp3"

    saved_path = save_audio(audio_bytes, output_file, target_dir=tmp_path)
    saved_path = Path(saved_path)

    assert saved_path.parent == tmp_path
    assert saved_path.suffix == ".mp3"
    assert saved_path.stem.startswith("output_")

    assert saved_path.read_bytes() == audio_bytes


def test_extract_speakers():
    transcript = "Alice: Hello\nBob: Hi\nAlice: How are you?"
    speakers = extract_speakers(transcript)
    assert set(speakers) == {"Alice", "Bob"}
