from unittest.mock import patch

from evals.audio_generation.src.utils.parsing_utils import get_transcripts


@patch("evals.audio_generation.src.utils.parsing_utils.INPUT_DIR")
@patch("evals.audio_generation.src.utils.parsing_utils.Path")
def test_get_transcripts(mock_path, mock_input_dir):
    mock_input_dir.__truediv__.return_value = mock_path
    mock_transcript_file = mock_path / "test_transcript.txt"
    mock_transcript_file.is_file.return_value = True
    mock_transcript_file.read_text.return_value = "Mock transcript content"

    result = get_transcripts("test_transcript.txt")

    mock_transcript_file.is_file.assert_called_once()
    mock_transcript_file.read_text.assert_called_once()
    assert result == "Mock transcript content"
