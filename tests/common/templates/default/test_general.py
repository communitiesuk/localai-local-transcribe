import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from common.templates.default.general import General
from common.database.postgres_models import DialogueEntry
from common.templates.utils.template_renderer import render_template
from unittest.mock import patch
from datetime import datetime, timezone



def test_prompt_with_agenda():
    transcript = [DialogueEntry(text="Hello", speaker="John"), DialogueEntry(text="Hi", speaker="Jane")]
    agenda = "1. Discuss project\n2. Plan next steps"

    result = General.prompt(transcript, agenda)

    assert result[0]["role"] == "system"

    prompt_body = result[0]["content"]
    transcript_messages = result[1]

    assert "4. Discussion Points" in prompt_body
    assert "- Err on the side of including more detail rather than less" in prompt_body
    assert "- Present in chronological order" not in prompt_body
    assert "2. Plan next steps" in prompt_body
    assert "- List any pending items for future discussion" in prompt_body
    assert "Hello" in transcript_messages["content"]
    assert "Here is the meeting transcript" in transcript_messages["content"]
 
    
def test_prompt_without_agenda():
    transcript = [DialogueEntry(text="Hello", speaker="John"), DialogueEntry(text="Hi", speaker="Jane")]

    result = General.prompt(transcript, None)

    assert result[0]["role"] == "system"

    prompt_body = result[0]["content"]
    transcript_messages = result[1]

    assert "- Err on the side of including more detail rather than less" in prompt_body
    assert "- Present in chronological order" in prompt_body
    assert "6. Action Items" in prompt_body
    assert "These are the agenda items for this meeting" not in prompt_body
    assert "Hi" in transcript_messages["content"]
    assert "Jane" in transcript_messages["content"]


def test_prompt_date_inclusion():
    transcript = []
    agenda = None

    fixed_time = datetime(2026, 5, 8, tzinfo=timezone.utc)

    with patch("common.templates.default.general.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_time
        result = General.prompt(transcript, None)

    assert "08 May 2026" in result[0]["content"]