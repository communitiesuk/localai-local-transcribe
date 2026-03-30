import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from backend.api.routes.transcriptions import (
    create_recording,
    create_transcription,
    delete_transcription,
    get_recordings_for_transcription,
    get_transcription,
    list_transcriptions,
    save_transcription,
)
from common.database.postgres_models import Transcription
from common.types import RecordingCreateRequest


@pytest.mark.asyncio
async def test_create_transcription_success(
    mocker,
    mock_session_with_recording,
    mock_user,
    mock_storage_service,  # noqa: ARG001
    mock_transcription_queue_service,
    transcription_request,
):
    """Test successful creation of a transcription job."""
    mock_transcription = Mock()
    mock_transcription.id = uuid.uuid4()
    mocker.patch("backend.api.routes.transcriptions.Transcription", return_value=mock_transcription)

    mock_minute = Mock()
    mock_minute.id = uuid.uuid4()
    mocker.patch("backend.api.routes.transcriptions.Minute", return_value=mock_minute)
    mocker.patch("backend.api.routes.transcriptions.MinuteVersion")

    response = await create_transcription(transcription_request, mock_session_with_recording, mock_user)

    assert response.id == mock_transcription.id
    assert mock_session_with_recording.add.call_count == 3
    mock_session_with_recording.commit.assert_awaited()
    mock_transcription_queue_service.publish_message.assert_called()


@pytest.mark.asyncio
async def test_create_transcription_file_not_found(
    mock_session_with_recording,
    mock_user,
    mock_storage_service,
    transcription_request,
):
    """Test error handling when the recording file is not found in S3."""
    mock_storage_service.check_object_exists = AsyncMock(return_value=False)

    with pytest.raises(HTTPException) as exception_info:
        await create_transcription(transcription_request, mock_session_with_recording, mock_user)

    assert exception_info.value.status_code == 404
    assert "Recording file not found in S3" in exception_info.value.detail


@pytest.mark.asyncio
async def test_create_recording_different_file_extensions(mocker, mock_session, mock_user):
    """Test creating recordings with different file extensions to ensure they are handled correctly."""

    for file_ext in ["mp3", "wav", "m4a", "webm"]:
        request = RecordingCreateRequest(file_extension=file_ext)

        mock_recording = Mock()
        mock_recording.id = uuid.uuid4()
        mock_recording.user_id = mock_user.id
        mock_recording.s3_file_key = f"uploads/{mock_user.email}/file.{file_ext}"

        mocker.patch("backend.api.routes.transcriptions.Recording", return_value=mock_recording)

        mock_session.refresh = AsyncMock()
        mock_session.add.reset_mock()
        mock_session.commit.reset_mock()

        mocker.patch("backend.api.routes.transcriptions.get_file_s3_key", return_value=mock_recording.s3_file_key)

        response = await create_recording(request, mock_session, mock_user)

        assert response.id == mock_recording.id
        assert file_ext in mock_recording.s3_file_key
        mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_get_recordings_for_transcription_unauthorized(mock_session, mock_user, mock_transcription):
    """Test error when user tries to access another user's transcription"""
    mock_transcription.user_id = 9
    mock_session.get = AsyncMock(return_value=mock_transcription)
    mock_user.id = 1

    with pytest.raises(HTTPException) as exception_info:
        await get_recordings_for_transcription(mock_transcription.id, mock_session, mock_user)

    assert exception_info.value.status_code == 404


@pytest.mark.asyncio
async def test_save_transcription_success(mock_session, mock_user, mock_transcription, transcription_patch_request):
    """Test successful save/update of a transcription"""
    mock_transcription.user_id = mock_user.id
    mock_transcription.title = "Local Transcription"
    mock_transcription.dialogue_entries = [{"speaker": "user_one", "text": "Hello World"}]

    mock_session.get = AsyncMock(return_value=mock_transcription)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    assert mock_transcription.title == "Local Transcription"

    response = await save_transcription(mock_transcription.id, transcription_patch_request, mock_session, mock_user)

    assert isinstance(response, Transcription) or response == mock_transcription
    assert mock_transcription.title == "Mocked Transcription Title"
    assert mock_transcription.dialogue_entries == transcription_patch_request.dialogue_entries

    mock_session.get.assert_awaited_once_with(Transcription, mock_transcription.id)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(mock_transcription)


@pytest.mark.asyncio
async def test_list_get_delete_transcription(mocker, mock_session, mock_user, mock_transcription):
    """Test listing, getting, and deleting a transcription."""


@pytest.mark.asyncio
async def test_list_transcriptions(mock_session, mock_user, mock_transcription):
    mock_session.exec = AsyncMock()
    mock_session.exec.side_effect = [Mock(one=Mock(return_value=1)), Mock(all=Mock(return_value=[mock_transcription]))]
    mock_transcription.dialogue_entries = [{"speaker": "Alice", "text": "Hello", "start_time": 0.0, "end_time": 1.0}]
    mock_transcription.status = "completed"
    mock_transcription.title = "Test Title"
    mock_transcription.created_datetime = mock_transcription.created_datetime

    result = await list_transcriptions(mock_session, mock_user, page=1, page_size=20)
    assert result.total_count == 1
    assert result.items[0].title == "Test Title"
    assert result.items[0].status == "completed"
    assert result.total_pages == 1


@pytest.mark.asyncio
async def test_get_transcription(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)
    response = await get_transcription(mock_transcription.id, mock_session, mock_user)
    assert response.id == mock_transcription.id
    assert response.title == mock_transcription.title


@pytest.mark.asyncio
async def test_delete_transcription(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)
    mock_session.delete = AsyncMock()
    mock_session.commit = AsyncMock()
    await delete_transcription(mock_transcription.id, mock_session, mock_user)
    mock_session.delete.assert_awaited_once_with(mock_transcription)
    mock_session.commit.assert_awaited_once()
