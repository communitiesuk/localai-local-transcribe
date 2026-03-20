from evals.audio_generation.src.utils.parsing_utils import build_pattern, extract_speakers, save_audio


def test_build_pattern():
    speakers = ["Alice", "Bob"]
    pattern = build_pattern(speakers)
    assert pattern == r"(Alice|Bob):\s*(.+?)(?=(Alice|Bob):|$)"


def test_save_audio(tmp_path):
    audio_bytes = b"test audio data"
    output_file = "output.mp3"

    saved_path = save_audio(audio_bytes, output_file, target_dir=tmp_path)
    expected_path = tmp_path / output_file

    assert saved_path == str(expected_path)
    assert expected_path.read_bytes() == audio_bytes


def test_extract_speakers():
    transcript = "Alice: Hello\nBob: Hi\nAlice: How are you?"
    speakers = extract_speakers(transcript)
    assert set(speakers) == {"Alice", "Bob"}
