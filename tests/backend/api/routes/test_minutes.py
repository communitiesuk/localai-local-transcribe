import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from datetime import datetime, UTC
from fastapi import HTTPException

from backend.api.routes.minutes import (
    list_minutes_for_transcription,
    create_minute,
    get_minute,
    list_minute_versions,
    create_minute_version,
    get_minute_version,
    delete_minute_version,
)

@pytest.fixture
def mock_user():
    user = Mock()
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.exec = AsyncMock()
    session.get = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_minute(mock_user):
    minute = Mock()
    minute.id = uuid.uuid4()
    minute.transcription_id = uuid.uuid4()
    minute.template_name = "TEMPLATE"
    minute.agenda = "AGENDA"
    minute.created_datetime = datetime.now(tz=UTC)
    minute.updated_datetime = datetime.now(tz=UTC)
    minute.transcription = Mock()
    minute.transcription.user_id = mock_user.id
    minute.minute_versions = []
    return minute


@pytest.fixture
def mock_minute_version(mock_minute):
    mock_minute_version = Mock()
    mock_minute_version.id = uuid.uuid4()
    mock_minute_version.minute_id = mock_minute.id
    mock_minute_version.status = "completed"
    mock_minute_version.created_datetime = datetime.now(tz=UTC)
    mock_minute_version.error = None
    mock_minute_version.ai_edit_instructions = None
    mock_minute_version.html_content = "<p>hi</p>"
    mock_minute_version.content_source = "initial_generation"
    mock_minute_version.minute = mock_minute
    return mock_minute_version

@pytest.mark.parametrize("handle_exception", [False, True])
@pytest.mark.asyncio
async def test_list_minutes_for_transcription_success(mock_session, mock_user, mock_minute,handle_exception):
    """ Test listing minutes for a transcription returns the correct data. """
    transcription = Mock()
    transcription.user_id = mock_user.id
    mock_session.get.return_value = transcription

    exec_result = Mock()
    exec_result.all.return_value = [mock_minute]
    mock_session.exec.return_value = exec_result

    if handle_exception:
        mock_session.get.return_value = None
        with pytest.raises(HTTPException):
            await list_minutes_for_transcription(mock_minute.transcription_id, mock_session, mock_user)
    else:

        result = await list_minutes_for_transcription(mock_minute.transcription_id, mock_session, mock_user)
        assert len(result) == 1
        assert result[0].id == mock_minute.id
        assert result[0].template_name == mock_minute.template_name

@pytest.mark.parametrize("handle_exception", [False, True])
@pytest.mark.asyncio
async def test_create_minute_success(mocker, mock_session, mock_user, handle_exception):
    """ Test creating a minute for a transcription successfully creates the minute and minute version. """
    transcription = Mock()
    transcription.user_id = mock_user.id
    mock_session.get.return_value = transcription

    test_uuid = uuid.uuid4()

    mock_minute_obj = Mock()
    mock_minute_obj.id = test_uuid
    mock_minute_version_obj = Mock()
    mock_minute_version_obj.id = uuid.uuid4()
    mocker.patch("backend.api.routes.minutes.Minute", return_value=mock_minute_obj)
    mocker.patch("backend.api.routes.minutes.MinuteVersion", return_value=mock_minute_version_obj)

    mock_llm = mocker.patch("backend.api.routes.minutes.llm_queue_service")
    request = SimpleNamespace(template_name="T", template_id=None, agenda="A")

    if handle_exception:
        mock_session.get.return_value = None
        with pytest.raises(HTTPException):
            await create_minute(transcription_id=mock_minute_obj.id, request=request, session=mock_session, user=mock_user)
    else:

        await create_minute(transcription_id=mock_minute_obj.id, request=request, session=mock_session, user=mock_user)

        assert mock_session.add.call_count == 2
        mock_session.commit.assert_awaited()
        mock_llm.publish_message.assert_called()


@pytest.mark.asyncio
async def test_get_minute_success(mock_session, mock_user, mock_minute):
    """ Test retrieving a minute by ID returns the correct minute. """
    exec_result = Mock()
    exec_result.first.return_value = mock_minute
    mock_session.exec.return_value = exec_result

    result = await get_minute(mock_minute.id, mock_session, mock_user)
    assert result is mock_minute


@pytest.mark.parametrize("handle_exception", [False, True])
@pytest.mark.asyncio
async def test_list_minute_versions_success(
    mock_session, mock_user, mock_minute, mock_minute_version, handle_exception
):
    """Test listing minute versions for a minute; also test the 404 branch."""
    exec_result = Mock()

    if handle_exception:
        exec_result.first.return_value = None
        mock_session.exec.return_value = exec_result

        with pytest.raises(HTTPException):
            await list_minute_versions(mock_minute.id, mock_session, mock_user)

    else:
        mock_minute.minute_versions = [mock_minute_version]
        exec_result.first.return_value = mock_minute
        mock_session.exec.return_value = exec_result

        result = await list_minute_versions(mock_minute.id, mock_session, mock_user)
        assert len(result) == 1
        assert result[0].id == mock_minute_version.id


@pytest.mark.asyncio
async def test_create_minute_version_success(mocker, mock_session, mock_user, mock_minute, mock_minute_version):
    """ Test creating a minute version successfully creates the version and returns the correct response. """
    mocker.patch("backend.api.routes.minutes.get_minute", return_value=mock_minute)

    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_minute_version.html_content = "<p>test_create_minute_version_success</p>"

    mock_llm = mocker.patch("backend.api.routes.minutes.llm_queue_service")
    mocker.patch("backend.api.routes.minutes.MinuteVersion", return_value=mock_minute_version)

    request = SimpleNamespace(content_source="initial_generation", html_content="<p>x</p>", ai_edit_instructions=None)

    reault = await create_minute_version(mock_minute.id, request, mock_session, mock_user)
    assert reault.minute_id == mock_minute.id
    assert reault.html_content == "<p>test_create_minute_version_success</p>"


@pytest.mark.parametrize("handle_exception", [False, True])
@pytest.mark.asyncio
async def test_get_minute_version_success(mock_session, mock_user, mock_minute_version, handle_exception):
    """ Test retrieving a minute version by ID returns the correct version. """
    exec_result = Mock()

    if handle_exception:
        mock_minute_version.minute.transcription.user_id = uuid.uuid4()  
        exec_result.first.return_value = mock_minute_version
        mock_session.exec.return_value = exec_result
        with pytest.raises(HTTPException):
            await get_minute_version(mock_minute_version.id, mock_session, mock_user)

    else:
        exec_result.first.return_value = mock_minute_version
        mock_session.exec.return_value = exec_result
        result = await get_minute_version(mock_minute_version.id, mock_session, mock_user)
        assert result is mock_minute_version


@pytest.mark.parametrize("handle_exception", [False, True])
@pytest.mark.asyncio
async def test_delete_minute_version_success(mock_session, mock_user, mock_minute_version, handle_exception):
    exec_result = Mock()
    if handle_exception:
        mock_minute_version.minute.transcription.user_id = uuid.uuid4()  
        exec_result.first.return_value = mock_minute_version
        mock_session.exec.return_value = exec_result
        with pytest.raises(HTTPException):
            await delete_minute_version(mock_minute_version.id, mock_session, mock_user)
        

    else:
        exec_result.first.return_value = mock_minute_version
        mock_session.exec.return_value = exec_result

        await delete_minute_version(mock_minute_version.id, mock_session, mock_user)
        mock_session.delete.assert_awaited_once_with(mock_minute_version)
        mock_session.commit.assert_awaited_once()
