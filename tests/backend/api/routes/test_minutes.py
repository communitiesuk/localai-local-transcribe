import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from typing import Any

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

from common.database.postgres_models import (
    Minute, 
    MinuteVersion,
    User,
    Transcription
)

#use actual Enum values
test_email= "tests@local-transcribe.gov.uk"

test_minute_obj = Minute(
    id=uuid.uuid4(),
    created_datetime=datetime.now(tz=UTC),
    updated_datetime=datetime.now(tz=UTC),
    transcription_id=uuid.uuid4(),
    template_name="TEMPLATE",
    user_template_id=None,
    agenda="AGENDA",
    minute_versions=[],
)

test_minute_version_obj = MinuteVersion(
    id=uuid.uuid4(),
    minute_id=test_minute_obj.id,  
    minute=test_minute_obj,                
    status="completed",
    created_datetime=datetime.now(tz=UTC),
    updated_datetime=datetime.now(tz=UTC),
    ai_edit_instructions=None,
    html_content="<p>hi</p>",
    content_source="initial_generation",
)

test_transcription_obj = Transcription(
    id=uuid.uuid4(),
    user_id=uuid.uuid4(),           
    audio_url="https://example.com/audio.mp3",
    status="completed",
    created_datetime=datetime.now(tz=UTC),
    updated_datetime=datetime.now(tz=UTC),
    minutes=[test_minute_obj],
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


@pytest.mark.asyncio
async def test_list_minutes_for_transcription_success(mock_session):
    user = User(id=uuid.uuid4(), email=test_email)  

    mock_minute = test_minute_obj
    mock_minute.transcription_id = user.id

    transcription = Mock()
    transcription.user_id = user.id
    mock_session.get.return_value = transcription

    exec_result = Mock()
    exec_result.all.return_value = [mock_minute]
    mock_session.exec.return_value = exec_result

    result = await list_minutes_for_transcription(mock_minute.transcription_id, mock_session, user)

    assert len(result) == 1
    assert result[0].id == mock_minute.id
    assert result[0].template_name == mock_minute.template_name


@pytest.mark.asyncio
async def test_list_minutes_for_transcription_not_found(mock_session):
    user = User(id=uuid.uuid4(), email=test_email) 

    mock_session.get.return_value = None
    mock_minute = test_minute_obj

    with pytest.raises(HTTPException) as exc_info:
        await list_minutes_for_transcription(mock_minute, mock_session, user)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_minute_success(mocker, mock_session):
    """Test creating a minute successfully creates the minute and minute version."""
    user_id = uuid.uuid4()
    user = User(id=user_id, email=test_email)  

    transcription = Mock()
    transcription.user_id = user.id
    mock_session.get.return_value = transcription

    mock_minute = test_minute_obj
    mock_minute_version = test_minute_version_obj

    mocker.patch("backend.api.routes.minutes.Minute", return_value=mock_minute)
    mocker.patch("backend.api.routes.minutes.MinuteVersion", return_value=mock_minute_version)

    mock_llm = mocker.patch("backend.api.routes.minutes.llm_queue_service")

    request = SimpleNamespace(template_name="T", template_id=None, agenda="A")

    await create_minute(
        transcription_id=mock_minute.id,
        request=request,
        session=mock_session,
        user=user,
    )

    assert mock_session.add.call_count == 2
    mock_session.commit.assert_awaited()
    mock_llm.publish_message.assert_called()

@pytest.mark.asyncio
async def test_create_minute_transcription_not_found(mocker, mock_session):
    """Test create_minute raises HTTPException when transcription is missing."""
    user = User(id=uuid.uuid4(), email=test_email)  
    mock_minute = test_minute_obj

    mock_session.get.return_value = None  

    request = SimpleNamespace(template_name="T", template_id=None, agenda="A")

    with pytest.raises(HTTPException) as exc_info:
        await create_minute(
            transcription_id=mock_minute.id,
            request=request,
            session=mock_session,
            user=user,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_minute_success(mock_session):
    """Test retrieving a minute by ID returns the correct minute."""
    user = User(id=uuid.uuid4(), email=test_email)

    fake_transcription = test_transcription_obj
    fake_transcription.user_id = user.id  

    mock_minute = test_minute_obj
    mock_minute.transcription_id = fake_transcription.id

    mock_minute.transcription = fake_transcription

    mock_session.get.return_value = fake_transcription

    exec_result = Mock()
    exec_result.first.return_value = mock_minute
    mock_session.exec.return_value = exec_result

    result = await get_minute(mock_minute.id, mock_session, user)

    assert result is mock_minute



@pytest.mark.asyncio
async def test_list_minute_versions_success(mock_session):
    user_id = uuid.uuid4()
    user = User(id=user_id, email=test_email)  

    exec_result = Mock()

    fake_transcription = test_transcription_obj
    fake_transcription.user_id = user.id 

    mock_minute = test_minute_obj
    mock_minute.transcription_id = fake_transcription.id
    mock_minute.transcription = fake_transcription

    mock_minute_version = test_minute_version_obj
    mock_minute.minute_versions = [mock_minute_version]

    exec_result.first.return_value = mock_minute
    mock_session.exec.return_value = exec_result

    result = await list_minute_versions(mock_minute.id, mock_session, user)

    assert len(result) == 1
    assert result[0].id == mock_minute_version.id

#from here

@pytest.mark.asyncio
async def test_list_minute_versions_not_found(mock_session):
    user_id = uuid.uuid4()
    user = User(id=user_id, email=test_email)  

    mock_minute = test_minute_obj

    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await list_minute_versions(mock_minute.id, mock_session, user)
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_minute_version_success(mocker, mock_session):
    """Test creating a minute version successfully creates the version and returns the correct response."""
    user_id = uuid.uuid4()
    user = User(id=user_id, email=test_email)  

    mock_minute = test_minute_obj
    mock_minute_version = test_minute_version_obj

    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    expected_html_content = "<p>test_create_minute_version_success</p>"
    mock_minute_version.html_content = expected_html_content

    mocker.patch("backend.api.routes.minutes.get_minute", return_value=mock_minute)
    mocker.patch("backend.api.routes.minutes.MinuteVersion", return_value=mock_minute_version)

    request = SimpleNamespace(content_source="initial_generation", html_content="<p>x</p>", ai_edit_instructions=None)

    result = await create_minute_version(mock_minute.id, request, mock_session, mock_user)
    assert result.minute_id == mock_minute.id
    assert result.html_content == expected_html_content


# @pytest.mark.asyncio
# async def test_delete_minute_version_success(mock_session, mock_user, mock_minute_version):
#     user_id = uuid.uuid4()
#     user = User(id=user_id, email=test_email) 

#     exec_result = Mock()
#     exec_result.first.return_value = mock_minute_version
#     mock_session.exec.return_value = exec_result

#     await delete_minute_version(mock_minute_version.id, mock_session, mock_user)

#     mock_session.delete.assert_awaited_once_with(mock_minute_version)
#     mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_minute_version_success(mock_session):
  
    user = User(id=uuid.uuid4(), email=test_email)

    fake_transcription = test_transcription_obj
    fake_transcription.user_id = user.id

    fake_minute = test_minute_obj
    fake_minute.transcription = fake_transcription
    fake_minute.transcription_id = fake_transcription.id    

    fake_minute_version = test_minute_version_obj
    fake_minute_version.minute = fake_minute
    fake_minute_version.minute_id = fake_minute.id

    exec_result = Mock()
    exec_result.first.return_value = fake_minute_version
    mock_session.exec.return_value = exec_result

    await delete_minute_version(fake_minute_version.id, mock_session, user)

    mock_session.delete.assert_awaited_once_with(fake_minute_version)
    mock_session.commit.assert_awaited_once()



@pytest.mark.asyncio
async def test_delete_minute_version_unauthorized(mock_session):
    user_id = uuid.uuid4()
    user = User(id=user_id, email=test_email)  

    fake_minute = test_minute_obj
    fake_minute.transcription = test_transcription_obj
    fake_minute.transcription_id = uuid.uuid4()

    fake_minute_version = test_minute_version_obj
    fake_minute_version.minute = fake_minute
    fake_minute_version.minute.transcription.user_id = uuid.uuid4()


    exec_result = Mock()
    exec_result.first.return_value = fake_minute_version
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_minute_version(fake_minute_version.id, mock_session, user)
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_minute_version_success(mock_session):

    user = User(id=uuid.uuid4(), email=test_email)

    fake_transcription = test_transcription_obj
    fake_transcription.user_id = user.id

    fake_minute = test_minute_obj
    fake_minute.transcription = fake_transcription
    fake_minute.transcription_id = fake_transcription.id    

    fake_minute_version = test_minute_version_obj
    fake_minute_version.minute = fake_minute
    fake_minute_version.minute_id = fake_minute.id
    
    exec_result = Mock()
    exec_result.first.return_value = fake_minute_version
    mock_session.exec.return_value = exec_result

    result = await get_minute_version(fake_minute_version.id, mock_session, user)
    assert result is fake_minute_version


@pytest.mark.asyncio
async def test_get_minute_version_unauthorized(mock_session):
    user = User(id=uuid.uuid4(), email=test_email)

    fake_transcription = test_transcription_obj
    fake_transcription.user_id = uuid.uuid4()

    fake_minute = test_minute_obj
    fake_minute.transcription = fake_transcription

    fake_minute_version = test_minute_version_obj
    fake_minute_version.minute = fake_minute

    exec_result = Mock()
    exec_result.first.return_value = fake_minute_version
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await get_minute_version(fake_minute_version.id, mock_session, user)

    assert exc_info.value.status_code == 404
