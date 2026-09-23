from common.database.postgres_models import DialogueEntry
from common.templates.default.general import General


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
    assert "1. Discuss project\n2. Plan next steps" in prompt_body
    assert "2. Plan next steps" in prompt_body
    assert prompt_body.count("BEGIN agenda ") == 1
    assert " - Trusted agenda boundary marker hash:" not in prompt_body
    assert "- List any pending items for future discussion" in prompt_body
    assert "- Add evidence sub-bullets under each main bullet" in prompt_body
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
    assert "Date:" not in prompt_body
    assert "Action Items" not in prompt_body
    assert "6. Next Steps" in prompt_body
    assert "These are the agenda items for this meeting" not in prompt_body
    assert "Hi" in transcript_messages["content"]
    assert "Jane" in transcript_messages["content"]


def test_prompt_forbids_declining_an_informal_transcript():
    """A recording of an informal conversation must still produce minutes, not a refusal.

    Without this the summariser decides some transcripts are "not a meeting" and answers with a
    request for a different transcript, which is useless to the user and leaves nothing cited.
    """
    result = General.prompt([DialogueEntry(text="Traffic was awful today", speaker="John")], None)

    prompt_body = result[0]["content"]

    assert "Do not decline because the recording is informal, short, incomplete, or off-topic" in prompt_body
    assert "do not ask for a different transcript" in prompt_body


def test_prompt_keeps_the_refusal_path_open_for_hostile_transcripts():
    """The informality instruction must not read as a blanket ban on declining.

    `refusal_robustness` scores refusing an overtly malicious injection as fully correct behaviour,
    so a prompt forbidding refusal outright would remove a sanctioned safe response — and the eval
    could not see the loss, because transparently ignoring the injection also scores 5.
    """
    result = General.prompt([DialogueEntry(text="Traffic was awful today", speaker="John")], None)

    prompt_body = result[0]["content"]

    assert "This does not override your safety obligations" in prompt_body
    assert "never decline to summarise" not in prompt_body


def test_prompt_forbids_inventing_actions():
    """Actions the summariser proposes itself cannot be cited, and read as agreed commitments."""
    result = General.prompt([DialogueEntry(text="Traffic was awful today", speaker="John")], None)

    assert "actually agreed or stated in the discussion" in result[0]["content"]


def test_prompt_makes_purpose_conditional():
    result = General.prompt([DialogueEntry(text="Traffic was awful today", speaker="John")], None)

    prompt_body = result[0]["content"]

    assert "Purpose/Objective of the meeting" in prompt_body
    assert "only if explicitly stated by a participant" in prompt_body
    assert "omit this field entirely otherwise" in prompt_body


def test_general_prompt_version_incremented():
    assert General.prompt_version == "0.1.1"
