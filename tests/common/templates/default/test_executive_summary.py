import pytest
from common.templates.default.executive_summary import ExecutiveSummary
from common.database.postgres_models import DialogueEntry
from common.templates.utils.template_renderer import render_template



def test_prompt_renders_template(expected_summary_prompt: str):
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



def test_template_renders_with_content(expected_summary_prompt: str):

    template = render_template("executive_summary.j2")
    block = template.blocks["prompt"]
    context = template.new_context()
    rendered_block = "".join(block(context))

    assert expected_summary_prompt in rendered_block
