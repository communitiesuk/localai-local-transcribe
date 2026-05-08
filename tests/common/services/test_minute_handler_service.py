from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest

from common.database.postgres_models import (
    DialogueEntry,
    Hallucination,
    JobStatus,
    Minute,
    MinuteVersion,
    Transcription,
    User,
    UserTemplate,
)
from common.services.minute_handler_service import (
    MinuteGenerationFailedError,
    MinuteHandlerService,
)
from common.settings import get_settings
from common.types import HallucinationType, LLMHallucination, MeetingType, MinuteAndHallucinations

mock_email = "tests@local-transcribe.com"
settings = get_settings()


@pytest.fixture
def mock_user() -> User:
    return User(
        id=uuid4(),
        email=mock_email,
        data_retention_days=30,
        created_datetime=datetime.now(UTC),
        updated_datetime=datetime.now(UTC),
    )


@pytest.fixture
def mock_dialogue_entry():
    return DialogueEntry(speaker="John", text="hello world", start_time=0.0, end_time=1.0)


@pytest.fixture
def mock_llm_hallucination():
    return LLMHallucination(
        hallucination_type=HallucinationType.NONSENSICAL,
        hallucination_text="this string is hallucinating",
        hallucination_reason="for reasons unknown",
    )


@pytest.fixture
def mock_minute():
    return Minute(
        id=uuid4(),
        transcription_id=uuid4(),
        template_name="Meeting summary",
        user_template_id=uuid4(),
        minute_versions=[],
    )


@pytest.fixture
def mock_minute_version(mock_minute):
    minute_version = MinuteVersion(
        id=uuid4(),
        minute_id=mock_minute.id,
        html_content="<p>existing minutes</p>",
        status=JobStatus.IN_PROGRESS,
        ai_edit_instructions="run a four minute mile",
    )
    minute_version.minute = mock_minute
    return minute_version


@pytest.fixture
def mock_session(mock_minute_version):
    session = Mock()
    session.get = Mock(return_value=mock_minute_version)
    session.add = Mock()
    session.commit = Mock()
    session.expunge = Mock()
    ctx = MagicMock()
    ctx.__enter__ = Mock(return_value=session)
    ctx.__exit__ = Mock(return_value=None)
    return ctx, session


@pytest.fixture
def mock_transcription(mock_minute, mock_user) -> Transcription:
    return Transcription(
        id=uuid4(),
        user_id=mock_user.id,
        audio_url="https://example.com/audio.mp3",
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        minutes=[mock_minute],
        title="Test Transcription",
        dialogue_entries=[mock_dialogue_entry],
    )


def test_convert_llm_hallucination_to_db_hallucination(mock_llm_hallucination, mock_minute_version):
    result = MinuteHandlerService.convert_llm_hallucination_to_db_hallucination(
        mock_llm_hallucination, mock_minute_version.id
    )

    assert isinstance(result, Hallucination)
    assert result.hallucination_text == mock_llm_hallucination.hallucination_text
    assert result.hallucination_reason == mock_llm_hallucination.hallucination_reason
    assert result.minute_version_id == mock_minute_version.id


def test_update_minute_version_updates_fields(mock_session, mock_minute_version):
    ctx, session = mock_session
    content = "<p>html content</p>"
    new_status = JobStatus.COMPLETED

    with patch("common.services.minute_handler_service.SessionLocal", return_value=ctx):
        MinuteHandlerService.update_minute_version(
            mock_minute_version.id,
            html_content=content,
            status=new_status,
            error=None,
            hallucinations=None,
        )

    assert mock_minute_version.html_content == content
    assert mock_minute_version.status == new_status
    session.add.assert_called_once_with(mock_minute_version)
    session.commit.assert_called_once()


def test_update_minute_version_raises_if_not_found(mock_session, mock_minute_version):
    ctx, session = mock_session
    session.get.return_value = None

    with (
        patch("common.services.minute_handler_service.SessionLocal", return_value=ctx),
        pytest.raises(ValueError, match=f"MinuteVersion not found for id: {mock_minute_version.id}"),
    ):
        MinuteHandlerService.update_minute_version(mock_minute_version.id)


def test_update_minute_version_converts_llm_hallucinations(mock_session, mock_minute_version, mock_llm_hallucination):
    ctx, session = mock_session

    with patch("common.services.minute_handler_service.SessionLocal", return_value=ctx):
        MinuteHandlerService.update_minute_version(
            mock_minute_version.id,
            hallucinations=[mock_llm_hallucination],
        )

    assert len(mock_minute_version.hallucinations) == 1
    assert isinstance(mock_minute_version.hallucinations[0], Hallucination)


@pytest.mark.asyncio
async def test_get_minute_version_returns_minute_version(mock_session, mock_minute_version):
    ctx, session = mock_session

    with patch("common.services.minute_handler_service.SessionLocal", return_value=ctx):
        result = await MinuteHandlerService.get_minute_version(mock_minute_version.id)

    assert result is mock_minute_version
    session.expunge.assert_called_once_with(mock_minute_version)


@pytest.mark.asyncio
async def test_get_minute_version_raises_if_not_found(mock_session):
    ctx, session = mock_session
    session.get.return_value = None

    with (
        patch("common.services.minute_handler_service.SessionLocal", return_value=ctx),
        pytest.raises(ValueError, match="MinuteVersion not found for id:"),
    ):
        await MinuteHandlerService.get_minute_version(uuid4())


@pytest.mark.asyncio
async def test_get_only_minute_version_raises_if_minute_not_found(mock_session):
    ctx, session = mock_session
    session.get.return_value = None

    with (
        patch("common.services.minute_handler_service.SessionLocal", return_value=ctx),
        pytest.raises(ValueError, match="Minute not found for minute id"),
    ):
        await MinuteHandlerService.get_only_minute_version_for_minute_id(uuid4())


@pytest.mark.asyncio
async def test_get_only_minute_version_raises_if_no_versions(mock_session, mock_minute):
    ctx, session = mock_session
    mock_minute.minute_versions = []

    session.get.return_value = mock_minute

    with (
        patch("common.services.minute_handler_service.SessionLocal", return_value=ctx),
        pytest.raises(ValueError, match="MinuteVersion not found for minute"),
    ):
        await MinuteHandlerService.get_only_minute_version_for_minute_id(uuid4())


@pytest.mark.asyncio
async def test_get_only_minute_version_raises_if_multiple_versions(mock_session, mock_minute, mock_minute_version):
    ctx, session = mock_session
    mock_minute.minute_versions = [mock_minute_version, mock_minute_version]
    session.get.return_value = mock_minute

    with (
        patch("common.services.minute_handler_service.SessionLocal", return_value=ctx),
        pytest.raises(ValueError, match="More than one MinuteVersions found"),
    ):
        await MinuteHandlerService.get_only_minute_version_for_minute_id(uuid4())


@pytest.mark.asyncio
async def test_get_only_minute_version_success(mock_session, mock_minute_version):
    ctx, session = mock_session

    mock_minute.minute_versions = [mock_minute_version]
    session.get.return_value = mock_minute

    with patch("common.services.minute_handler_service.SessionLocal", return_value=ctx):
        result = await MinuteHandlerService.get_only_minute_version_for_minute_id(uuid4())

    assert result == mock_minute_version
    session.expunge.assert_called_once_with(mock_minute)


def test_predict_meeting_too_short(mock_dialogue_entry):
    dialogue_too_short = ("a " * (settings.MIN_WORD_COUNT_FOR_SUMMARY - 1)).strip()

    mock_dialogue_entry["text"] = dialogue_too_short
    result = MinuteHandlerService.predict_meeting([mock_dialogue_entry])
    assert result == MeetingType.too_short


def test_predict_meeting_standard(mock_dialogue_entry):
    valid_dialogue = ("a " * (settings.MIN_WORD_COUNT_FOR_FULL_SUMMARY + 1)).strip()

    mock_dialogue_entry["text"] = valid_dialogue
    result = MinuteHandlerService.predict_meeting([mock_dialogue_entry])
    assert result == MeetingType.standard


def test_handle_bad_transcript(mock_dialogue_entry, mocker):
    utterance = "Adam says hello world"
    mocker.patch(
        "common.services.minute_handler_service.transcript_as_speaker_and_utterance",
        return_value=utterance,
    )
    result = MinuteHandlerService.handle_bad_transcript([mock_dialogue_entry])

    assert f"Transcript is: {utterance}" in result.text
    assert result.hallucinations == []


@pytest.mark.asyncio
async def test_generate_basic_minutes(mock_dialogue_entry, mocker):
    chatbot_output = "I am a chatbot"
    mock_chatbot = AsyncMock()
    mock_chatbot.chat = AsyncMock(return_value=chatbot_output)
    mock_chatbot.hallucination_check = AsyncMock(return_value=[])
    mocker.patch("common.services.minute_handler_service.create_default_chatbot", return_value=mock_chatbot)

    result = await MinuteHandlerService.generate_basic_minutes([mock_dialogue_entry])

    assert result.text == chatbot_output
    assert result.hallucinations == []
    mock_chatbot.chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_edit_minutes_with_ai(mock_dialogue_entry, mocker):
    text_content = "edited minutes"
    mock_chatbot = AsyncMock()
    mock_chatbot.chat = AsyncMock(return_value=text_content)
    mock_chatbot.hallucination_check = AsyncMock(return_value=[])
    mocker.patch("common.services.minute_handler_service.create_default_chatbot", return_value=mock_chatbot)

    result = await MinuteHandlerService.edit_minutes_with_ai(
        minutes="<p>original minutes</p>",
        edit_instructions="make it shorter",
        transcript=[mock_dialogue_entry],
    )

    assert result.text == text_content
    assert result.hallucinations == []


@pytest.mark.asyncio
async def test_edit_minutes_with_ai_strips_code_fences(mock_dialogue_entry, mocker):
    chatbot_output = "edited minutes"
    mock_chatbot = AsyncMock()
    mock_chatbot.chat = AsyncMock(return_value=f"```html<p>{chatbot_output}</p>```")
    mock_chatbot.hallucination_check = AsyncMock(return_value=[])
    mocker.patch("common.services.minute_handler_service.create_default_chatbot", return_value=mock_chatbot)

    result = await MinuteHandlerService.edit_minutes_with_ai(
        minutes="<p>original minutes</p>",
        edit_instructions="make it shorter",
        transcript=[mock_dialogue_entry],
    )

    assert result.text == f"<p>{chatbot_output}</p>"


@pytest.mark.asyncio
async def test_generate_minutes_too_short(mocker, mock_minute, mock_transcription):
    output = "too short"
    mock_minute.transcription = mock_transcription

    mocker.patch.object(
        MinuteHandlerService,
        "handle_bad_transcript",
        return_value=MinuteAndHallucinations(text=output, total_claims=0, hallucinations=[]),
    )
    mocker.patch("common.services.minute_handler_service.mistune.html", return_value=f"<p>{output}</p>")

    result = await MinuteHandlerService.generate_minutes(MeetingType.too_short, mock_minute)

    assert result.text == f"<p>{output}</p>"
    assert result.hallucinations == []


@pytest.mark.asyncio
async def test_generate_minutes_short(mocker, mock_minute, mock_transcription):
    output = "short"
    mock_minute.transcription = mock_transcription

    mocker.patch.object(
        MinuteHandlerService,
        "generate_basic_minutes",
        AsyncMock(return_value=MinuteAndHallucinations(text=output, total_claims=0, hallucinations=[])),
    )
    mocker.patch("common.services.minute_handler_service.mistune.html", return_value=f"<p>{output}</p>")

    result = await MinuteHandlerService.generate_minutes(MeetingType.short, mock_minute)

    assert result.text == f"<p>{output}</p>"


@pytest.mark.asyncio
async def test_generate_minutes_standard(mocker, mock_dialogue_entry, mock_minute, mock_transcription):
    output = "standard"

    mock_minute.transcription = mock_transcription
    mock_minute.transcription.dialogue_entries = [mock_dialogue_entry]

    mocker.patch.object(
        MinuteHandlerService,
        "generate_full_minutes",
        AsyncMock(return_value=MinuteAndHallucinations(text=output, total_claims=0, hallucinations=[])),
    )
    mocker.patch("common.services.minute_handler_service.mistune.html", return_value=f"<p>{output}</p>")

    result = await MinuteHandlerService.generate_minutes(MeetingType.standard, mock_minute)

    assert result.text == f"<p>{output}</p>"


@pytest.mark.asyncio
async def test_generate_minutes_raises_if_no_dialogue(mock_minute, mock_transcription):
    mock_minute.transcription = mock_transcription
    mock_minute.transcription.dialogue_entries = []

    with pytest.raises(MinuteGenerationFailedError) as exc_info:
        await MinuteHandlerService.generate_minutes(MeetingType.standard, mock_minute)
    assert f"Minute {mock_minute.id} has no dialogue entries" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_full_minutes_uses_user_template(mocker, mock_minute):
    output = "backwards_parallelogram"
    mock_template = AsyncMock()

    mocker.patch.object(
        MinuteHandlerService,
        "generate_minute_from_user_template",
        AsyncMock(return_value=MinuteAndHallucinations(text=output, total_claims=0, hallucinations=[])),
    )
    mocker.patch("common.services.minute_handler_service.TemplateManager.get_template", return_value=mock_template)

    mocker.patch("common.services.minute_handler_service.convert_american_to_british_spelling", return_value=output)

    result = await MinuteHandlerService.generate_full_minutes(mock_minute)

    assert result.text == output
    MinuteHandlerService.generate_minute_from_user_template.assert_awaited_once_with(mock_minute)


@pytest.mark.asyncio
async def test_generate_full_minutes_uses_default_template(mocker, mock_minute):
    output = "expected_result"

    mock_template = AsyncMock()
    mock_template.generate = AsyncMock(
        return_value=MinuteAndHallucinations(text="result", total_claims=0, hallucinations=[])
    )
    mock_minute.user_template_id = None
    mocker.patch("common.services.minute_handler_service.TemplateManager.get_template", return_value=mock_template)
    mocker.patch("common.services.minute_handler_service.convert_american_to_british_spelling", return_value=output)

    result = await MinuteHandlerService.generate_full_minutes(mock_minute)

    assert result.text == output
    mock_template.generate.assert_awaited_once_with(mock_minute)


@pytest.mark.asyncio
async def test_generate_minute_from_user_template_success(mocker, mock_session, mock_minute, mock_transcription):
    output = "minute contents"
    ctx, session = mock_session
    mock_template = Mock(spec=UserTemplate)
    session.get.return_value = mock_template

    mock_minute.transcription = mock_transcription

    mocker.patch("common.services.minute_handler_service.SessionLocal", return_value=ctx)
    mocker.patch(
        "common.services.minute_handler_service.generate_user_template",
        AsyncMock(return_value=MinuteAndHallucinations(text=output, total_claims=0, hallucinations=[])),
    )

    result = await MinuteHandlerService.generate_minute_from_user_template(mock_minute)

    assert result.text == output
    assert result.hallucinations == []


@pytest.mark.asyncio
async def test_generate_minute_from_user_template_raises_if_no_template(mocker, mock_minute, mock_session):
    ctx, session = mock_session
    session.get.return_value = None

    mocker.patch("common.services.minute_handler_service.SessionLocal", return_value=ctx)

    with pytest.raises(RuntimeError, match=f"No template with id {mock_minute.user_template_id}"):
        await MinuteHandlerService.generate_minute_from_user_template(mock_minute)


@pytest.mark.asyncio
async def test_process_minute_generation_message_success(
    mocker, mock_minute_version, mock_minute, mock_transcription, mock_dialogue_entry
):
    mock_minute.transcription = mock_transcription
    mock_minute.transcription.dialogue_entries = [mock_dialogue_entry]
    dialogue = "<p>the family table</p>"

    mocker.patch.object(MinuteHandlerService, "get_minute_version", AsyncMock(return_value=mock_minute_version))
    mocker.patch.object(MinuteHandlerService, "predict_meeting", return_value=MeetingType.standard)
    mocker.patch.object(
        MinuteHandlerService,
        "generate_minutes",
        AsyncMock(return_value=MinuteAndHallucinations(text=dialogue, total_claims=0, hallucinations=[])),
    )
    mocker.patch.object(MinuteHandlerService, "update_minute_version")

    await MinuteHandlerService.process_minute_generation_message(mock_minute_version.id)

    MinuteHandlerService.update_minute_version.assert_called_once_with(
        mock_minute_version.id,
        html_content=dialogue,
        hallucinations=[],
        status=JobStatus.COMPLETED,
    )


@pytest.mark.asyncio
async def test_process_minute_generation_message_fails_if_no_dialogue(
    mocker, mock_minute_version, mock_minute, mock_transcription
):
    mock_minute.transcription = mock_transcription
    mock_minute.transcription.dialogue_entries = []

    mocker.patch.object(MinuteHandlerService, "get_minute_version", AsyncMock(return_value=mock_minute_version))
    mocker.patch.object(MinuteHandlerService, "update_minute_version")

    with pytest.raises(MinuteGenerationFailedError) as exc_info:
        await MinuteHandlerService.process_minute_generation_message(mock_minute_version.id)
    assert f"Transcription for minute {mock_minute.id} has no dialogue entries" in str(exc_info.value.__cause__)

    MinuteHandlerService.update_minute_version.assert_called_with(
        mock_minute_version.id, status=JobStatus.FAILED, error=mocker.ANY
    )


@pytest.mark.asyncio
async def test_process_minute_generation_message_raises_if_minute_version_not_found(mock_minute_version, mocker):
    mocker.patch.object(MinuteHandlerService, "get_minute_version", AsyncMock(side_effect=ValueError("not found")))

    with pytest.raises(MinuteGenerationFailedError):
        await MinuteHandlerService.process_minute_generation_message(mock_minute_version.id)


@pytest.mark.asyncio
async def test_process_minute_edit_message_success(
    mocker, mock_minute_version, mock_minute, mock_transcription, mock_dialogue_entry
):
    output = "edited_string"
    mock_minute.transcription = mock_transcription
    mock_minute.transcription.dialogue_entries = [mock_dialogue_entry]

    target = MinuteVersion(
        id=uuid4(),
        minute_id=uuid4(),
        html_content=mock_minute_version.html_content,
        status=mock_minute_version.status,
        ai_edit_instructions=mock_minute_version.ai_edit_instructions,
    )

    target.minute = mock_minute_version.minute

    mocker.patch.object(
        MinuteHandlerService, "get_minute_version", AsyncMock(side_effect=[mock_minute_version, target])
    )
    mocker.patch.object(
        MinuteHandlerService,
        "edit_minutes_with_ai",
        AsyncMock(return_value=MinuteAndHallucinations(text=output, total_claims=0, hallucinations=[])),
    )
    mocker.patch.object(MinuteHandlerService, "update_minute_version")

    await MinuteHandlerService.process_minute_edit_message(mock_minute_version.id, target.id)

    MinuteHandlerService.update_minute_version.assert_called_once_with(
        minute_version_id=target.id,
        status=JobStatus.COMPLETED,
        html_content=output,
        hallucinations=[],
    )


@pytest.mark.asyncio
async def test_process_minute_edit_message_raises_if_no_edit_instructions(mocker, mock_minute_version):
    target = MinuteVersion(
        id=uuid4(),
        minute_id=uuid4(),
        ai_edit_instructions=None,
    )

    mocker.patch.object(
        MinuteHandlerService, "get_minute_version", AsyncMock(side_effect=[mock_minute_version, target])
    )

    with pytest.raises(MinuteGenerationFailedError, match="Target minute does not have AI edit instructions"):
        await MinuteHandlerService.process_minute_edit_message(mock_minute_version.id, target.id)


@pytest.mark.asyncio
async def test_process_minute_edit_message_raises_if_no_transcript(
    mocker,
    mock_minute_version,
    mock_transcription,
):
    mock_minute.transcription = mock_transcription
    mock_transcription.dialogue_entries = None

    target = MinuteVersion(
        id=uuid4(),
        minute_id=uuid4(),
        ai_edit_instructions="make it shorter",
    )
    target.minute = mock_minute_version.minute

    mocker.patch.object(
        MinuteHandlerService, "get_minute_version", AsyncMock(side_effect=[mock_minute_version, target])
    )
    mocker.patch.object(MinuteHandlerService, "update_minute_version")

    with pytest.raises(MinuteGenerationFailedError) as exc_info:
        await MinuteHandlerService.process_minute_edit_message(mock_minute_version.id, target.id)

    assert "Source minute version has no transcript" in str(exc_info.value.__cause__)
