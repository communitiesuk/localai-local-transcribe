from unittest.mock import patch, MagicMock
from pathlib import Path
from evals.audio_generation.src.utils.write_dialogue import write_dialogue
from evals.audio_generation.src.utils.parsing_utils import get_transcripts
from evals.audio_generation.src.utils.dialogue import DialogueEntry

@patch("evals.audio_generation.src.utils.write_dialogue.Path.write_text")
@patch("evals.audio_generation.src.utils.write_dialogue.Path.mkdir")
def test_write_dialogue(mock_mkdir, mock_write_text):
    entries = [
        DialogueEntry(speaker="Alice", text="Hello", start_time="00:00:01", end_time="00:00:02"),
        DialogueEntry(speaker="Bob", text="Hi", start_time="00:00:03", end_time="00:00:04"),
    ]
    output_path = Path("/mock/output/dialogue.json")

    write_dialogue(entries, output_path)

    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_write_text.assert_called_once()
    written_data = mock_write_text.call_args[0][0]


