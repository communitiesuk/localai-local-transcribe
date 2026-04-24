import uuid
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


@pytest.mark.asyncio
async def test_list_minutes_for_transcription_success(mock_session, mock_minute, mock_user):
    minute = mock_minute

    transcription = Mock()
    transcription.user_id = mock_user.id
    mock_session.get.return_value = transcription

    exec_result = Mock()
    exec_result.all.return_value = [minute]
    mock_session.exec.return_value = exec_result

    result = await list_minutes_for_transcription(minute.transcription_id, mock_session, mock_user)

    assert len(result) == 1
    assert result[0].id == minute.id
    assert result[0].template_name == minute.template_name


@pytest.mark.asyncio
async def test_list_minutes_for_transcription_not_found(mock_session, mock_user):
    mock_session.get.return_value = None
    transcription_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await list_minutes_for_transcription(transcription_id, mock_session, mock_user)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_minute_success(mocker, mock_session, mock_minute, mock_minute_version, mock_user):
    """Test creating a minute successfully creates the minute and minute version."""

    transcription = Mock()
    transcription.user_id = mock_user.id
    mock_session.get.return_value = transcription

    minute = mock_minute
    minute_version = mock_minute_version

    mocker.patch("backend.api.routes.minutes.Minute", return_value=minute)
    mocker.patch("backend.api.routes.minutes.MinuteVersion", return_value=minute_version)

    llm = mocker.patch("backend.api.routes.minutes.llm_queue_service")

    request = SimpleNamespace(template_name="T", template_id=None, agenda="A")

    await create_minute(
        transcription_id=minute.id,
        request=request,
        session=mock_session,
        user=mock_user,
    )

    mock_session.add.assert_any_call(minute)
    mock_session.add.assert_any_call(minute_version)
    mock_session.commit.assert_awaited()
    llm.publish_message.assert_called()


@pytest.mark.asyncio
async def test_create_minute_transcription_not_found(mock_session, mock_minute, mock_user):
    """Test create_minute raises HTTPException when transcription is missing."""
    minute = mock_minute

    mock_session.get.return_value = None

    request = SimpleNamespace(template_name="T", template_id=None, agenda="A")

    with pytest.raises(HTTPException) as exc_info:
        await create_minute(
            transcription_id=minute.id,
            request=request,
            session=mock_session,
            user=mock_user,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_minute_success(mock_session, mock_minute, mock_transcription, mock_user):
    """Test retrieving a minute by ID returns the correct minute."""

    transcription = mock_transcription
    transcription.user_id = mock_user.id

    minute = mock_minute
    minute.transcription_id = transcription.id

    minute.transcription = transcription

    mock_session.get.return_value = transcription

    exec_result = Mock()
    exec_result.first.return_value = minute
    mock_session.exec.return_value = exec_result

    result = await get_minute(minute.id, mock_session, mock_user)

    assert result is minute


@pytest.mark.asyncio
async def test_list_minute_versions_success(
    mock_session, mock_minute, mock_minute_version, mock_transcription, mock_user
):
    transcription = mock_transcription
    transcription.user_id = mock_user.id

    minute = mock_minute
    minute.transcription_id = transcription.id
    minute.transcription = transcription

    minute_version = mock_minute_version
    minute.minute_versions = [minute_version]

    exec_result_versions = Mock()
    exec_result_versions.first.return_value = minute

    exec_result_hallucinations = Mock()
    exec_result_hallucinations.all.return_value = []

    mock_session.exec.side_effect = [exec_result_versions, exec_result_hallucinations]

    result = await list_minute_versions(minute.id, mock_session, mock_user)

    assert len(result) == 1
    assert result[0].id == minute_version.id
    assert result[0].hallucinations_detected is False


@pytest.mark.asyncio
async def test_list_minute_versions_not_found(mock_session, mock_minute, mock_user):
    minute = mock_minute

    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await list_minute_versions(minute.id, mock_session, mock_user)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_minute_version_success(mocker, mock_session, mock_minute, mock_minute_version, mock_user):
    """Test creating a minute version successfully creates the version and returns the correct response."""

    minute = mock_minute
    minute_version = mock_minute_version

    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    expected_html_content = "<p>mock_create_minute_version_success</p>"
    minute_version.html_content = expected_html_content

    mocker.patch("backend.api.routes.minutes.get_minute", return_value=minute)
    mocker.patch("backend.api.routes.minutes.MinuteVersion", return_value=minute_version)

    request = SimpleNamespace(content_source="initial_generation", html_content="<p>x</p>", ai_edit_instructions=None)

    result = await create_minute_version(minute.id, request, mock_session, mock_user)
    assert result.minute_id == minute.id
    assert result.html_content == expected_html_content


@pytest.mark.asyncio
async def test_delete_minute_version_success(
    mock_session, mock_minute, mock_minute_version, mock_transcription, mock_user
):
    transcription = mock_transcription
    transcription.user_id = mock_user.id

    minute = mock_minute
    minute.transcription = transcription
    minute.transcription_id = transcription.id

    minute_version = mock_minute_version
    minute_version.minute = minute
    minute_version.minute_id = minute.id

    exec_result = Mock()
    exec_result.first.return_value = minute_version
    mock_session.exec.return_value = exec_result

    await delete_minute_version(minute_version.id, mock_session, mock_user)

    mock_session.delete.assert_awaited_once_with(minute_version)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_minute_version_unauthorized(
    mock_session, mock_minute, mock_minute_version, mock_transcription, mock_user
):
    minute = mock_minute
    minute.transcription = mock_transcription
    minute.transcription_id = uuid.uuid4()

    minute_version = mock_minute_version
    minute_version.minute = minute
    minute_version.minute.transcription.user_id = uuid.uuid4()

    exec_result = Mock()
    exec_result.first.return_value = minute_version
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_minute_version(minute_version.id, mock_session, mock_user)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_minute_version_success(
    mock_session, mock_minute, mock_minute_version, mock_transcription, mock_user
):
    transcription = mock_transcription
    transcription.user_id = mock_user.id

    minute = mock_minute
    minute.transcription = transcription
    minute.transcription_id = transcription.id

    minute_version = mock_minute_version
    minute_version.minute = minute
    minute_version.minute_id = minute.id

    exec_result = Mock()
    exec_result.first.return_value = minute_version
    mock_session.exec.return_value = exec_result

    result = await get_minute_version(minute_version.id, mock_session, mock_user)
    assert result is minute_version


@pytest.mark.asyncio
async def test_get_minute_version_unauthorized(
    mock_session, mock_minute, mock_minute_version, mock_transcription, mock_user
):
    transcription = mock_transcription
    transcription.user_id = uuid.uuid4()

    minute = mock_minute
    minute.transcription = transcription

    minute_version = mock_minute_version
    minute_version.minute = minute

    exec_result = Mock()
    exec_result.first.return_value = minute_version
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await get_minute_version(minute_version.id, mock_session, mock_user)

    assert exc_info.value.status_code == 404
