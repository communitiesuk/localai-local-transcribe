from common.database.postgres_models import DialogueEntry
from common.prompts import (
    format_guidelines,
    get_ai_edit_initial_messages,
    get_basic_minutes_prompt,
    get_chat_with_transcript_system_message,
    get_cite_claims_prompt,
    get_extract_claims_prompt,
    get_meeting_detection_prompt,
    get_meeting_title_prompt,
    get_minutes_messages,
    get_section_for_agenda_prompt,
    get_sections_from_transcript_prompt,
    get_transcript_messages,
    string_to_system_message,
)

_TRANSCRIPT: list[DialogueEntry] = [
    {"speaker": "Alice", "text": "Hello everyone.", "start_time": 0.0},
    {"speaker": "Bob", "text": "Good morning.", "start_time": 5.0},
]


def test_get_transcript_messages_role_and_content():
    result = get_transcript_messages(_TRANSCRIPT)
    assert result["role"] == "user"
    assert "Alice" in result["content"]
    assert "Hello everyone." in result["content"]


def test_get_minutes_messages_role_and_content():
    result = get_minutes_messages("Some minutes text")
    assert result["role"] == "user"
    assert "Some minutes text" in result["content"]


def test_get_ai_edit_initial_messages_structure():
    messages = get_ai_edit_initial_messages("My minutes", "Fix the grammar", _TRANSCRIPT)
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "user"
    assert "Fix the grammar" in messages[3]["content"]
    assert "Alice" in messages[1]["content"]
    assert "My minutes" in messages[2]["content"]


def test_get_chat_with_transcript_system_message():
    result = get_chat_with_transcript_system_message(_TRANSCRIPT)
    assert result["role"] == "system"
    assert "Alice" in result["content"]
    assert "citation" in result["content"]


def test_get_basic_minutes_prompt_structure():
    messages = get_basic_minutes_prompt(_TRANSCRIPT)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "summary" in messages[0]["content"].lower()
    assert messages[1]["role"] == "user"


def test_get_sections_from_transcript_prompt_structure():
    messages = get_sections_from_transcript_prompt(_TRANSCRIPT)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "sections" in messages[0]["content"]


def test_get_meeting_detection_prompt_structure():
    messages = get_meeting_detection_prompt(_TRANSCRIPT)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "long meeting" in messages[0]["content"]


def test_get_section_for_agenda_prompt():
    result = get_section_for_agenda_prompt("Budget Review")
    assert result["role"] == "user"
    assert "Budget Review" in result["content"]


def test_get_extract_claims_prompt():
    messages = get_extract_claims_prompt("The budget is £1 million.")
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert "The budget is £1 million." in messages[0]["content"]
    assert "claims" in messages[0]["content"].lower()


def test_get_extract_claims_prompt_excludes_document_metadata():
    """The document date comes from the app, not the transcript, so it is not a claim to cite.

    Extracting it guarantees an uncited claim on every minute, which surfaces to the user as a
    hallucination that isn't one.
    """
    content = get_extract_claims_prompt("Date: 28 July 2026")[0]["content"]

    assert "document metadata" in content.lower()


def test_get_extract_claims_prompt_still_extracts_the_meeting_purpose():
    """A purpose the summariser invented is the fabrication a reader is least likely to question.

    The extractor only ever sees the draft, never the transcript, so it cannot tell an invented
    purpose from a grounded one — excluding "the summariser's own characterisation" therefore drops
    both, and an unsupported purpose statement is never checked against the transcript at all.
    """
    content = get_extract_claims_prompt("The purpose of the meeting was to approve the budget.")[0]["content"]

    assert "the purpose of the meeting was to" in content.lower()
    assert "ARE claims and must be extracted" in content


def test_get_cite_claims_prompt():
    messages = get_cite_claims_prompt("Draft text.", ["The budget is £1m"], _TRANSCRIPT)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    content = messages[0]["content"]
    assert "Draft text." in content
    assert "The budget is £1m" in content
    assert "Alice" in content


def test_get_cite_claims_prompt_asks_for_both_sides_of_an_exchange():
    """An elliptical reply cited alone reads as unsupported without the turn that prompted it."""
    content = get_cite_claims_prompt("Draft text.", ["Masha has custody"], _TRANSCRIPT)[0]["content"]

    assert "cite both entries" in content


def test_string_to_system_message():
    result = string_to_system_message("You are helpful.")
    assert result == {"role": "system", "content": "You are helpful."}


def test_get_meeting_title_prompt():
    messages = get_meeting_title_prompt(_TRANSCRIPT)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert "Alice" in messages[0]["content"]
    assert "title" in messages[0]["content"].lower()


def test_format_guidelines_list():
    result = format_guidelines(["Be concise", "Use UK English"])
    assert result == "- Be concise\n- Use UK English"


def test_format_guidelines_string():
    result = format_guidelines("Already formatted")
    assert result == "Already formatted"
