from common.database.postgres_models import DialogueEntry
from common.templates.default.care_assessment_v2 import CareAssessmentV2
from common.templates.default.template_prompts.eligibility_criteria import ELIGIBILITY_CRITERIA

transcript = [
    DialogueEntry(text="Discuss project", speaker="Alice"),
    DialogueEntry(text="Plan next steps", speaker="Bob"),
]
result = CareAssessmentV2.prompt(transcript, None)
prompt = result[0]["content"]


def test_prompt_renders_template():
    assert "## Health, Environment, and Safety" in prompt
    assert "Care Act outcomes" in prompt
    assert "What is your daily routine?" in prompt


def test_prompt_includes_eligibility_criteria():
    assert ELIGIBILITY_CRITERIA[0]["title"] in prompt
    assert ELIGIBILITY_CRITERIA[1]["guidance"] in prompt


def test_prompt_transcript_inclusion():
    content = result[1]["content"]

    assert "Discuss project" in content
    assert "Plan next steps" in content
    assert "Alice" in content
