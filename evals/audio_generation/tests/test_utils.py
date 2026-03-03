from evals.audio_generation.utils.build_pattern import build_pattern
from evals.audio_generation.utils.extract_speakers import extract_speakers
from evals.audio_generation.utils.save_audio import save_audio


def test_build_pattern():
    speakers = ["Alice", "Bob"]
    pattern = build_pattern(speakers)
    assert pattern == r"(Alice|Bob):\s*(.+?)(?=(Alice|Bob):|$)"


def test_save_audio(tmp_path):
    audio_bytes = b"test audio data"
    output_file = tmp_path / "output.mp3"
    saved_path = save_audio(audio_bytes, str(output_file))
    assert saved_path == str(output_file)
    assert output_file.read_bytes() == audio_bytes


def test_extract_speakers():
    transcript = "Alice: Hello\nBob: Hi\nAlice: How are you?"
    speakers = extract_speakers(transcript)
    assert set(speakers) == {"Alice", "Bob"}
