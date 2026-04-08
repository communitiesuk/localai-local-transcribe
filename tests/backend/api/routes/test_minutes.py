import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from backend.api.routes.minutes import (
    create_minute,
    create_minute_version,
    delete_minute_version,
    get_minute,
    get_minute_version,
    list_minute_versions,
    list_minutes_for_transcription,
)
from common.database.postgres_models import ContentSource, JobStatus, Minute, MinuteVersion, Transcription, User

test_email = "tests@local-transcribe.gov.uk"


@pytest.fixture
def test_user() -> User:
    return User(
        id=uuid.uuid4(),
        email=test_email,
    )


@pytest.fixture
def test_minute() -> Minute:
    return Minute(
        id=uuid.uuid4(),
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        transcription_id=uuid.uuid4(),
        template_name="TEMPLATE",
        user_template_id=None,
        agenda="AGENDA",
        minute_versions=[],
    )


@pytest.fixture
def test_minute_version(test_minute) -> MinuteVersion:
    return MinuteVersion(
        id=uuid.uuid4(),
        minute_id=test_minute.id,
        minute=test_minute,
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        ai_edit_instructions=None,
        html_content="<p>hello world</p>",
        content_source=ContentSource.INITIAL_GENERATION,
    )


@pytest.fixture
def test_transcription(test_minute) -> Transcription:
    return Transcription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        audio_url="https://example.com/audio.mp3",
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        minutes=[test_minute],
    )


@pytest.fixture
def mock_session():
    mock_session = AsyncMock()
    mock_session.exec = AsyncMock()
    mock_session.get = AsyncMock()
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.delete = AsyncMock()
    return mock_session


@pytest.mark.asyncio
async def test_list_minutes_for_transcription_success(mock_session, test_minute, test_user):
    minute = test_minute
    minute.transcription_id = test_user.id

    transcription = Mock()
    transcription.user_id = test_user.id
    mock_session.get.return_value = transcription

    exec_result = Mock()
    exec_result.all.return_value = [minute]
    mock_session.exec.return_value = exec_result

    result = await list_minutes_for_transcription(minute.transcription_id, mock_session, test_user)

    assert len(result) == 1
    assert result[0].id == minute.id
    assert result[0].template_name == minute.template_name


@pytest.mark.asyncio
async def test_list_minutes_for_transcription_not_found(mock_session, test_minute, test_user):
    mock_session.get.return_value = None
    minute = test_minute

    with pytest.raises(HTTPException) as exc_info:
        await list_minutes_for_transcription(minute, mock_session, test_user)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_minute_success(mocker, mock_session, test_minute, test_minute_version, test_user):
    """Test creating a minute successfully creates the minute and minute version."""

    transcription = Mock()
    transcription.user_id = test_user.id
    mock_session.get.return_value = transcription

    minute = test_minute
    minute_version = test_minute_version

    mocker.patch("backend.api.routes.minutes.Minute", return_value=minute)
    mocker.patch("backend.api.routes.minutes.MinuteVersion", return_value=minute_version)

    llm = mocker.patch("backend.api.routes.minutes.llm_queue_service")

    request = SimpleNamespace(template_name="T", template_id=None, agenda="A")

    await create_minute(
        transcription_id=minute.id,
        request=request,
        session=mock_session,
        user=test_user,
    )

    assert mock_session.add.call_count == 2
    mock_session.commit.assert_awaited()
    llm.publish_message.assert_called()


@pytest.mark.asyncio
async def test_create_minute_transcription_not_found(mock_session, test_minute, test_user):
    """Test create_minute raises HTTPException when transcription is missing."""
    minute = test_minute

    mock_session.get.return_value = None

    request = SimpleNamespace(template_name="T", template_id=None, agenda="A")

    with pytest.raises(HTTPException) as exc_info:
        await create_minute(
            transcription_id=minute.id,
            request=request,
            session=mock_session,
            user=test_user,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_minute_success(mock_session, test_minute, test_transcription, test_user):
    """Test retrieving a minute by ID returns the correct minute."""

    transcription = test_transcription
    transcription.user_id = test_user.id

    minute = test_minute
    minute.transcription_id = transcription.id

    minute.transcription = transcription

    mock_session.get.return_value = transcription

    exec_result = Mock()
    exec_result.first.return_value = minute
    mock_session.exec.return_value = exec_result

    result = await get_minute(minute.id, mock_session, test_user)

    assert result is minute


@pytest.mark.asyncio
async def test_list_minute_versions_success(
    mock_session, test_minute, test_minute_version, test_transcription, test_user
):
    exec_result = Mock()

    transcription = test_transcription
    transcription.user_id = test_user.id

    minute = test_minute
    minute.transcription_id = transcription.id
    minute.transcription = transcription

    minute_version = test_minute_version
    minute.minute_versions = [minute_version]

    exec_result.first.return_value = minute
    mock_session.exec.return_value = exec_result

    result = await list_minute_versions(minute.id, mock_session, test_user)

    assert len(result) == 1
    assert result[0].id == minute_version.id


@pytest.mark.asyncio
async def test_list_minute_versions_not_found(mock_session, test_minute, test_user):
    minute = test_minute

    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await list_minute_versions(minute.id, mock_session, test_user)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_minute_version_success(mocker, mock_session, test_minute, test_minute_version, test_user):
    """Test creating a minute version successfully creates the version and returns the correct response."""

    minute = test_minute
    minute_version = test_minute_version

    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    expected_html_content = "<p>test_create_minute_version_success</p>"
    minute_version.html_content = expected_html_content

    mocker.patch("backend.api.routes.minutes.get_minute", return_value=minute)
    mocker.patch("backend.api.routes.minutes.MinuteVersion", return_value=minute_version)

    request = SimpleNamespace(content_source="initial_generation", html_content="<p>x</p>", ai_edit_instructions=None)

    result = await create_minute_version(minute.id, request, mock_session, test_user)
    assert result.minute_id == minute.id
    assert result.html_content == expected_html_content


@pytest.mark.asyncio
async def test_delete_minute_version_success(
    mock_session, test_minute, test_minute_version, test_transcription, test_user
):
    transcription = test_transcription
    transcription.user_id = test_user.id

    minute = test_minute
    minute.transcription = transcription
    minute.transcription_id = transcription.id

    minute_version = test_minute_version
    minute_version.minute = minute
    minute_version.minute_id = minute.id

    exec_result = Mock()
    exec_result.first.return_value = minute_version
    mock_session.exec.return_value = exec_result

    await delete_minute_version(minute_version.id, mock_session, test_user)

    mock_session.delete.assert_awaited_once_with(minute_version)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_minute_version_unauthorized(
    mock_session, test_minute, test_minute_version, test_transcription, test_user
):
    minute = test_minute
    minute.transcription = test_transcription
    minute.transcription_id = uuid.uuid4()

    minute_version = test_minute_version
    minute_version.minute = minute
    minute_version.minute.transcription.user_id = uuid.uuid4()

    exec_result = Mock()
    exec_result.first.return_value = minute_version
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_minute_version(minute_version.id, mock_session, test_user)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_minute_version_success(
    mock_session, test_minute, test_minute_version, test_transcription, test_user
):
    transcription = test_transcription
    transcription.user_id = test_user.id

    minute = test_minute
    minute.transcription = transcription
    minute.transcription_id = transcription.id

    minute_version = test_minute_version
    minute_version.minute = minute
    minute_version.minute_id = minute.id

    exec_result = Mock()
    exec_result.first.return_value = minute_version
    mock_session.exec.return_value = exec_result

    result = await get_minute_version(minute_version.id, mock_session, test_user)
    assert result is minute_version


@pytest.mark.asyncio
async def test_get_minute_version_unauthorized(
    mock_session, test_minute, test_minute_version, test_transcription, test_user
):
    transcription = test_transcription
    transcription.user_id = uuid.uuid4()

    minute = test_minute
    minute.transcription = transcription

    minute_version = test_minute_version
    minute_version.minute = minute

    exec_result = Mock()
    exec_result.first.return_value = minute_version
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await get_minute_version(minute_version.id, mock_session, test_user)

    assert exc_info.value.status_code == 404
