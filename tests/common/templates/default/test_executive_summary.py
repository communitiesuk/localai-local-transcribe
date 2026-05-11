from common.database.postgres_models import DialogueEntry
from common.templates.default.executive_summary import ExecutiveSummary


def test_prompt_renders_template():
    transcript = [DialogueEntry(text="Hello", speaker="John"), DialogueEntry(text="Hi", speaker="Jane")]

    result = ExecutiveSummary.prompt(transcript, None)

    assert result[0]["role"] == "system"

    prompt_body = result[0]["content"]
    transcript_messages = result[1]

    assert "British English spelling and conventions" in prompt_body
    assert "Do not hallucinate" in prompt_body
    assert "bulleted list for clarity" in prompt_body
    assert "Hello" in transcript_messages["content"]
    assert "Jane" in transcript_messages["content"]
