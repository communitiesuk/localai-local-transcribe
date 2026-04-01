import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

import backend.api.routes.chat as chat_module


@pytest.fixture
def mock_user():
    user = Mock()
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def mock_session():
    s = AsyncMock()
    s.get = AsyncMock()
    s.exec = AsyncMock()
    s.add = Mock()
    s.commit = AsyncMock()
    s.refresh = AsyncMock()
    s.delete = AsyncMock()
    return s


@pytest.fixture(autouse=True)
def patch_llm_queue_service(monkeypatch):
    mock_queue = Mock()
    monkeypatch.setattr(chat_module, "llm_queue_service", mock_queue)
    return mock_queue


def make_chat(id=None, user_content="u", assistant_content="a", status="completed"):
    c = Mock()
    c.id = id or uuid.uuid4()
    c.user_content = user_content
    c.assistant_content = assistant_content
    c.status = status
    c.created_datetime = datetime.now(timezone.utc)
    c.updated_datetime = datetime.now(timezone.utc)
    return c


def make_transcription(user_id):
    t = Mock()
    t.id = uuid.uuid4()
    t.user_id = user_id
    return t


@pytest.mark.asyncio
async def test_list_chat_success_and_not_found(mock_session, mock_user):
    # success: transcription exists and belongs to user
    transcription = make_transcription(mock_user.id)
    chat = make_chat()
    result = Mock()
    result.all.return_value = [chat]

    mock_session.get.return_value = transcription
    mock_session.exec.return_value = result

    res = await chat_module.list_chat(transcription.id, mock_session, mock_user)
    assert len(res.chat) == 1
    assert res.chat[0].id == chat.id

    # not found: transcription missing
    mock_session.get.return_value = None
    with pytest.raises(HTTPException):
        await chat_module.list_chat(transcription.id, mock_session, mock_user)


@pytest.mark.asyncio
async def test_create_chat_commits_and_publishes(mock_session, mock_user, patch_llm_queue_service):
    transcription = make_transcription(mock_user.id)
    mock_session.get.return_value = transcription

    req = SimpleNamespace(user_content="hello")

    res = await chat_module.create_chat(transcription.id, req, mock_session, mock_user)

    # ensure a Chat was added and DB committed/refreshed
    assert mock_session.add.called
    mock_session.commit.assert_awaited()
    mock_session.refresh.assert_awaited()

    # queue should have publish_message called with the created id
    patch_llm_queue_service.publish_message.assert_called()
    assert res.id is not None


@pytest.mark.asyncio
async def test_get_chat_variants(mock_session, mock_user):
    transcription = make_transcription(mock_user.id)
    mock_session.get.side_effect = [transcription, None]

    # chat missing -> raises
    with pytest.raises(HTTPException):
        await chat_module.get_chat(transcription.id, uuid.uuid4(), mock_session, mock_user)

    # now return a chat
    chat = make_chat()
    mock_session.get.side_effect = [transcription, chat]
    res = await chat_module.get_chat(transcription.id, chat.id, mock_session, mock_user)
    assert res.id == chat.id
    assert res.user_content == chat.user_content


@pytest.mark.asyncio
async def test_delete_chat_and_not_found(mock_session, mock_user):
    transcription = make_transcription(mock_user.id)
    chat = make_chat()
    mock_session.exec.return_value = Mock()

    # success path
    mock_session.get.side_effect = [transcription, chat]
    await chat_module.delete_chat(transcription.id, chat.id, mock_session, mock_user)
    mock_session.delete.assert_awaited()
    mock_session.commit.assert_awaited()

    # transcription not found
    mock_session.get.reset_mock()
    mock_session.get.return_value = None
    with pytest.raises(HTTPException):
        await chat_module.delete_chat(transcription.id, chat.id, mock_session, mock_user)


@pytest.mark.asyncio
async def test_delete_chats_and_not_found(mock_session, mock_user):
    transcription = make_transcription(mock_user.id)

    # success path
    mock_session.get.return_value = transcription
    exec_result = Mock()
    mock_session.exec.return_value = exec_result
    await chat_module.delete_chats(transcription.id, mock_session, mock_user)
    mock_session.exec.assert_awaited()
    mock_session.commit.assert_awaited()

    # not found path
    mock_session.get.return_value = None
    with pytest.raises(HTTPException):
        await chat_module.delete_chats(transcription.id, mock_session, mock_user)
