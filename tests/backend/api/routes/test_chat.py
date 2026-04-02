import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from datetime import datetime, timezone
from fastapi import HTTPException


from backend.api.routes.chat import (
    create_chat,
    delete_chat,
    get_chat,
    list_chat,
)


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
    monkeypatch.setattr("backend.api.routes.chat.llm_queue_service", mock_queue)
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
    transcription = make_transcription(mock_user.id)
    chat = make_chat()
    result = Mock()
    result.all.return_value = [chat]

    mock_session.get.return_value = transcription
    mock_session.exec.return_value = result

    res = await list_chat(transcription.id, mock_session, mock_user)
    assert len(res.chat) == 1
    assert res.chat[0].id == chat.id

    mock_session.get.return_value = None
    with pytest.raises(HTTPException):
        await list_chat(transcription.id, mock_session, mock_user)


@pytest.mark.asyncio
async def test_create_chat_commits_and_publishes(mock_session, mock_user, patch_llm_queue_service):
    transcription = make_transcription(mock_user.id)
    mock_session.get.return_value = transcription

    req = SimpleNamespace(user_content="hello")

    res = await create_chat(transcription.id, req, mock_session, mock_user)

    assert mock_session.add.called
    mock_session.commit.assert_awaited()
    mock_session.refresh.assert_awaited()

    patch_llm_queue_service.publish_message.assert_called()
    assert res.id is not None


@pytest.mark.asyncio
async def test_get_chat_variants(mock_session, mock_user):
    transcription = make_transcription(mock_user.id)
    mock_session.get.side_effect = [transcription, None]

    with pytest.raises(HTTPException):
        await get_chat(transcription.id, uuid.uuid4(), mock_session, mock_user)

    chat = make_chat()
    mock_session.get.side_effect = [transcription, chat]
    res = await get_chat(transcription.id, chat.id, mock_session, mock_user)
    assert res.id == chat.id
    assert res.user_content == chat.user_content


@pytest.mark.asyncio
async def test_delete_chat_success(mock_session, mock_user):
    transcription = make_transcription(mock_user.id)
    chat = make_chat()

    mock_session.get = AsyncMock(side_effect=[transcription, chat])

    await delete_chat(
        transcription.id,
        chat.id,
        mock_session,
        mock_user,
    )

    mock_session.delete.assert_awaited_once_with(chat)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_chat_transcription_not_found(mock_session, mock_user):
    mock_session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await delete_chat(
            uuid.uuid4(),
            uuid.uuid4(),
            mock_session,
            mock_user,
        )

    assert exc.value.status_code == 404


# is there a bug with the caller?
# @pytest.mark.asyncio
# async def test_delete_chats_and_not_found(mock_session, mock_user):
#     transcription = make_transcription(mock_user.id)

#     mock_session.get.return_value = transcription
#     exec_result = Mock()
#     mock_session.exec.return_value = exec_result
#     await delete_chats(transcription.id, mock_session, mock_user)
#     mock_session.exec.assert_awaited()
#     mock_session.commit.assert_awaited()

#     mock_session.get.return_value = None
#     with pytest.raises(HTTPException):
#         await delete_chats(transcription.id, mock_session, mock_user)
