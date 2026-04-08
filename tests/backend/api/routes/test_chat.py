import uuid
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


def make_mock_get(transcription, chat):
    async def mock_get(model, _id):
        if model.__name__ == "Transcription":
            return transcription
        if model.__name__ == "Chat":
            return chat
        return None

    return mock_get


@pytest.mark.asyncio
async def test_list_chat_success(mock_session, make_user, make_chat, make_transcription):
    make_transcription.user_id = make_user.id

    result = Mock()
    result.all.return_value = [make_chat]

    mock_session.get.return_value = make_transcription
    mock_session.exec.return_value = result

    res = await list_chat(make_transcription.id, mock_session, make_user)

    assert len(res.chat) == 1
    assert res.chat[0].id == make_chat.id
    mock_session.exec.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_chat_raises_when_transcription_not_found(mock_session, make_user, make_transcription):
    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        await list_chat(make_transcription.id, mock_session, make_user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_chat_success(
    mock_session, make_user, patch_llm_queue_service, make_transcription, mocker, make_chat
):
    make_transcription.user_id = make_user.id
    mock_session.get.return_value = make_transcription

    req = SimpleNamespace(user_content="hello")
    mocker.patch("backend.api.routes.chat.Chat", return_value=make_chat)

    res = await create_chat(make_transcription.id, req, mock_session, make_user)

    assert res.id == make_chat.id
    mock_session.add.assert_called_once_with(make_chat)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(make_chat)
    patch_llm_queue_service.publish_message.assert_called_once_with(ANY)


@pytest.mark.asyncio
async def test_create_chat_raises_when_transcription_not_found(
    mock_session,
    make_user,
    mocker,
):
    mock_session.get.return_value = None

    req = SimpleNamespace(user_content="hello")
    mocker.patch("backend.api.routes.chat.Chat", return_value=Mock())

    with pytest.raises(HTTPException) as exc:
        await create_chat(uuid.uuid4(), req, mock_session, make_user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_chat_raises_when_user_does_not_match_transcription(
    mock_session,
    make_user,
    make_transcription,
    mocker,
):
    transcription = make_transcription
    transcription.user_id = uuid.uuid4()
    mock_session.get.return_value = transcription

    req = SimpleNamespace(user_content="hello")
    mocker.patch("backend.api.routes.chat.Chat", return_value=Mock())

    with pytest.raises(HTTPException) as exc:
        await create_chat(transcription.id, req, mock_session, make_user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_chat_raises_when_transcription_not_found(
    mock_session,
    make_user,
    make_chat,
):
    mock_session.get.side_effect = make_mock_get(None, make_chat)

    with pytest.raises(HTTPException) as exc:
        await get_chat(uuid.uuid4(), uuid.uuid4(), mock_session, make_user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_chat_raises_when_user_does_not_match_transcription(
    mock_session,
    make_user,
    make_transcription,
    make_chat,
):
    make_transcription.user_id = uuid.uuid4()
    mock_session.get.side_effect = make_mock_get(make_transcription, make_chat)

    with pytest.raises(HTTPException) as exc:
        await get_chat(make_transcription.id, make_chat.id, mock_session, make_user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_chat_raises_when_chat_not_found(
    mock_session,
    make_user,
    make_transcription,
):
    make_transcription.user_id = make_user.id
    mock_session.get.side_effect = make_mock_get(make_transcription, None)

    with pytest.raises(HTTPException):
        await get_chat(make_transcription.id, uuid.uuid4(), mock_session, make_user)


@pytest.mark.asyncio
async def test_get_chat_success(
    mock_session,
    make_user,
    make_transcription,
    make_chat,
):
    make_transcription.user_id = make_user.id
    mock_session.get.side_effect = make_mock_get(make_transcription, make_chat)

    res = await get_chat(make_transcription.id, make_chat.id, mock_session, make_user)

    assert res.id == make_chat.id
    assert res.user_content == make_chat.user_content


@pytest.mark.asyncio
async def test_delete_chat_success(mock_session, make_user, make_chat, make_transcription):
    make_transcription.user_id = make_user.id

    mock_session.get = AsyncMock(side_effect=[make_transcription, make_chat])

    await delete_chat(
        make_transcription.id,
        make_chat.id,
        mock_session,
        make_user,
    )

    mock_session.delete.assert_awaited_once_with(make_chat)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_chat_transcription_not_found(mock_session, make_user):
    mock_session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await delete_chat(
            uuid.uuid4(),
            uuid.uuid4(),
            mock_session,
            make_user,
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_chats_and_not_found(mock_session, make_user, make_transcription):
    make_transcription.user_id = make_user.id

    mock_session.get.return_value = make_transcription
    exec_result = Mock()
    mock_session.exec.return_value = exec_result
    await delete_chats(make_transcription.id, mock_session, make_user)
    mock_session.exec.assert_awaited()
    mock_session.commit.assert_awaited()

    mock_session.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await delete_chats(make_transcription.id, mock_session, make_user)
    assert exc.value.status_code == 404
