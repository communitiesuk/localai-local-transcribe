from unittest.mock import patch
from evals.audio_generation.src.utils.parsing_utils import get_transcripts
import json

@patch("evals.audio_generation.src.utils.parsing_utils.INPUT_DIR")
@patch("evals.audio_generation.src.utils.parsing_utils.Path")
def test_get_transcripts(mock_path, mock_input_dir):
    mock_input_dir.__truediv__.return_value = mock_path

    mock_transcript_file = mock_path / "test_transcript.json"
    mock_transcript_file.is_file.return_value = True

    mock_json = [
        {
            "speaker": "Alice",
            "text": " Hello ",
            "start_time": 0.0,
            "end_time": 1.0,
        }
    ]

    mock_transcript_file.read_text.return_value = json.dumps(mock_json)

    result = get_transcripts("test_transcript.json")

    mock_transcript_file.is_file.assert_called_once()
    mock_transcript_file.read_text.assert_called_once()

    assert len(result) == 1
    assert result[0].speaker == "Alice"
    assert result[0].text == "Hello"  
    assert result[0].start_time == 0.0
    assert result[0].end_time == 1.0
