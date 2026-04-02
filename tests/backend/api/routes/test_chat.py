import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, Mock

import pytest
from fastapi import HTTPException

from backend.api.routes.chat import (
    create_chat,
    delete_chat,
    delete_chats,
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
    session = AsyncMock()
    session.get = AsyncMock()
    session.exec = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture(autouse=True)
def patch_llm_queue_service(monkeypatch):
    mock_queue = Mock()
    monkeypatch.setattr("backend.api.routes.chat.llm_queue_service", mock_queue)
    return mock_queue


def make_chat(uid=None, user_content="hello", assistant_content="world", status="completed"):
    chat = Mock()
    chat.id = uid or uuid.uuid4()
    chat.user_content = user_content
    chat.assistant_content = assistant_content
    chat.status = status
    chat.created_datetime = datetime.now(UTC)
    chat.updated_datetime = datetime.now(UTC)
    return chat


def make_transcription(user_id):
    transcription = Mock()
    transcription.id = uuid.uuid4()
    transcription.user_id = user_id
    return transcription


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
@pytest.mark.parametrize(
    ("transcription_exists", "user_matches", "should_raise"),
    [
        (True, True, False),
        (False, True, True),
        (True, False, True),
    ],
)
async def test_create_chat_branches(
    mock_session,
    mock_user,
    patch_llm_queue_service,
    mocker,
    transcription_exists,
    user_matches,
    should_raise,
):
    req = SimpleNamespace(user_content="hello")

    if transcription_exists:
        user_id = mock_user.id if user_matches else uuid.uuid4()
        transcription = make_transcription(user_id)
        mock_session.get.return_value = transcription
    else:
        mock_session.get.return_value = None
        transcription = None

    mock_chat = Mock()
    mock_chat.id = uuid.uuid4()
    mocker.patch("backend.api.routes.chat.Chat", return_value=mock_chat)

    if should_raise:
        with pytest.raises(HTTPException):
            await create_chat(
                uuid.uuid4() if transcription is None else transcription.id,
                req,
                mock_session,
                mock_user,
            )
    else:
        res = await create_chat(
            transcription.id,
            req,
            mock_session,
            mock_user,
        )

        assert res.id == mock_chat.id
        mock_session.add.assert_called_once_with(mock_chat)
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(mock_chat)
        patch_llm_queue_service.publish_message.assert_called_once_with(ANY)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("transcription_exists", "user_matches", "chat_exists", "should_raise"),
    [
        (False, True, False, True),
        (True, False, False, True),
        (True, True, False, True),
        (True, True, True, False),
    ],
)
async def test_get_chat_all_branches(
    mock_session,
    mock_user,
    transcription_exists,
    user_matches,
    chat_exists,
    should_raise,
):
    async def mock_get(model, _id) -> Mock | None:
        if model.__name__ == "Transcription":
            return transcription
        if model.__name__ == "Chat":
            return chat
        return None

    if transcription_exists:
        user_id = mock_user.id if user_matches else uuid.uuid4()
        transcription = make_transcription(user_id)
    else:
        transcription = None

    chat = make_chat() if chat_exists else None

    mock_session.get.side_effect = mock_get

    if should_raise:
        with pytest.raises(HTTPException):
            await get_chat(
                uuid.uuid4(),
                uuid.uuid4(),
                mock_session,
                mock_user,
            )
    else:
        res = await get_chat(
            transcription.id,
            chat.id,
            mock_session,
            mock_user,
        )

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


@pytest.mark.asyncio
async def test_delete_chats_and_not_found(mock_session, mock_user):
    transcription = make_transcription(mock_user.id)

    mock_session.get.return_value = transcription
    exec_result = Mock()
    mock_session.exec.return_value = exec_result
    await delete_chats(transcription.id, mock_session, mock_user)
    mock_session.exec.assert_awaited()
    mock_session.commit.assert_awaited()

    mock_session.get.return_value = None
    with pytest.raises(HTTPException):
        await delete_chats(transcription.id, mock_session, mock_user)
