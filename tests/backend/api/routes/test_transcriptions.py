import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from backend.api.routes.transcriptions import (
    create_recording,
    create_transcription,
    delete_transcription,
    get_recordings_for_transcription,
    get_transcription,
    list_labelled_transcriptions,
    list_unlabelled_transcriptions,
    rename_speaker_everywhere,
    update_dialogue_entry_speaker,
    update_dialogue_entry_text,
    update_transcription_title,
)
from common.database.postgres_models import JobStatus
from common.types import (
    RecordingCreateRequest,
    RenameSpeakerRequest,
    UpdateDialogueEntrySpeakerRequest,
    UpdateDialogueEntryTextRequest,
    UpdateTranscriptionTitleRequest,
)


@pytest.mark.asyncio
async def test_create_transcription_success(
    mocker,
    mock_session_with_recording,
    mock_user,
    mock_transcription_queue_service,
    mock_minute,
    mock_minute_version,
    transcription_request,
    mock_transcription,
    mock_storage_service,  # NOQA: ARG001
):
    """Test successful creation of a transcription with associated minute and minute version."""
    mocker.patch("backend.api.routes.transcriptions.Transcription", return_value=mock_transcription)
    mocker.patch("backend.api.routes.transcriptions.Minute", return_value=mock_minute)
    mocker.patch("backend.api.routes.transcriptions.MinuteVersion", return_value=mock_minute_version)

    response = await create_transcription(transcription_request, mock_session_with_recording, mock_user)

    assert response.id == mock_transcription.id
    mock_session_with_recording.add.assert_any_call(mock_transcription)
    mock_session_with_recording.add.assert_any_call(mock_minute)
    mock_session_with_recording.add.assert_any_call(mock_minute_version)
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


@pytest.mark.parametrize("file_format", ["mp3", "wav", "m4a", "webm"])
@pytest.mark.asyncio
async def test_create_recording_different_file_extensions(
    mocker,
    mock_session,
    mock_user,
    mock_storage_service,  # NOQA: ARG001
    file_format,
    mock_recording,
):
    """Test creating recordings with different file extensions to ensure they are handled correctly."""

    request = RecordingCreateRequest(file_extension=file_format)

    mock_recording.s3_file_key = f"uploads/{mock_user.email}/file.{file_format}"

    mocker.patch("backend.api.routes.transcriptions.Recording", return_value=mock_recording)
    mocker.patch("backend.api.routes.transcriptions.get_file_s3_key", return_value=mock_recording.s3_file_key)

    response = await create_recording(request, mock_session, mock_user)

    assert response.id == mock_recording.id
    assert file_format in mock_recording.s3_file_key
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_recordings_for_transcription_unauthorized(mock_session, mock_user, mock_transcription):
    """Test error when user tries to access another user's transcription"""
    mock_transcription.user_id = uuid.uuid4()
    mock_session.get = AsyncMock(return_value=mock_transcription)

    with pytest.raises(HTTPException) as exception_info:
        await get_recordings_for_transcription(mock_transcription.id, mock_session, mock_user)

    assert exception_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_recordings_for_transcription_success(
    mock_session, mock_user, mock_transcription, mock_storage_service, mock_recording
):
    mock_user.id = mock_transcription.user_id

    mock_recording.created_datetime = datetime.now(UTC)

    mock_result = Mock()
    mock_result.all.return_value = [mock_recording]

    mock_session.get = AsyncMock(return_value=mock_transcription)
    mock_session.exec = AsyncMock(return_value=mock_result)

    mock_storage_service.generate_presigned_url_get_object = AsyncMock(return_value="signed-url")
    response = await get_recordings_for_transcription(mock_transcription.id, mock_session, mock_user)

    assert len(response) == 1
    assert response[0].id == mock_recording.id
    assert response[0].url == "signed-url"


@pytest.mark.asyncio
async def test_update_transcription_title_success(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    await update_transcription_title(
        mock_transcription.id,
        UpdateTranscriptionTitleRequest(title="Updated title"),
        mock_session,
        mock_user,
    )

    assert mock_transcription.title == "Updated title"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_transcription_title_null_succeeds_no_change(mock_session, mock_user, mock_transcription):
    original_title = mock_transcription.title
    mock_session.get = AsyncMock(return_value=mock_transcription)

    await update_transcription_title(
        mock_transcription.id,
        UpdateTranscriptionTitleRequest(title=None),
        mock_session,
        mock_user,
    )

    assert mock_transcription.title == original_title
    mock_session.commit.assert_not_awaited()  # No commit should be made since no change was made


@pytest.mark.asyncio
async def test_update_transcription_title_not_found(mock_session, mock_user):
    mock_session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await update_transcription_title(
            uuid.uuid4(),
            UpdateTranscriptionTitleRequest(title="Updated title"),
            mock_session,
            mock_user,
        )

    assert exc.value.status_code == 404
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_transcription_title_unauthorized(mock_session, mock_user, mock_transcription):
    mock_transcription.user_id = uuid.uuid4()
    mock_session.get = AsyncMock(return_value=mock_transcription)

    with pytest.raises(HTTPException) as exc:
        await update_transcription_title(
            mock_transcription.id,
            UpdateTranscriptionTitleRequest(title="Updated title"),
            mock_session,
            mock_user,
        )

    assert exc.value.status_code == 404
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_rename_speaker_everywhere_success(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    await rename_speaker_everywhere(
        mock_transcription.id,
        RenameSpeakerRequest(original_speaker="Alice", new_speaker="Alicia"),
        mock_session,
        mock_user,
    )

    assert mock_transcription.dialogue_entries == [
        {"speaker": "Alicia", "text": "Hello", "start_time": 0.0, "end_time": 1.0},
        {"speaker": "Bob", "text": "Hi there", "start_time": 1.0, "end_time": 2.0},
    ]
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_dialogue_entry_speaker_success(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    await update_dialogue_entry_speaker(
        mock_transcription.id,
        1,
        UpdateDialogueEntrySpeakerRequest(
            new_speaker="Robert",
            expected_speaker="Bob",
            expected_start_time=1.0,
            expected_end_time=2.0,
        ),
        mock_session,
        mock_user,
    )

    assert mock_transcription.dialogue_entries == [
        {"speaker": "Alice", "text": "Hello", "start_time": 0.0, "end_time": 1.0},
        {"speaker": "Robert", "text": "Hi there", "start_time": 1.0, "end_time": 2.0},
    ]
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_dialogue_entry_timestamp_conflict(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    with pytest.raises(HTTPException) as exc:
        await update_dialogue_entry_speaker(
            mock_transcription.id,
            1,
            UpdateDialogueEntrySpeakerRequest(
                new_speaker="Robert",
                expected_start_time=999.0,
                expected_end_time=2.0,
            ),
            mock_session,
            mock_user,
        )

    assert exc.value.status_code == 409
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_dialogue_entry_speaker_conflict(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    with pytest.raises(HTTPException) as exc:
        await update_dialogue_entry_speaker(
            mock_transcription.id,
            1,
            UpdateDialogueEntrySpeakerRequest(
                new_speaker="Robert",
                expected_speaker="NotBob",
                expected_start_time=1.0,
                expected_end_time=2.0,
            ),
            mock_session,
            mock_user,
        )

    assert exc.value.status_code == 409
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("entry_index", [-1, 99])
async def test_update_dialogue_entry_speaker_not_found(mock_session, mock_user, mock_transcription, entry_index):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    with pytest.raises(HTTPException) as exc:
        await update_dialogue_entry_speaker(
            mock_transcription.id,
            entry_index,
            UpdateDialogueEntrySpeakerRequest(new_speaker="Robert"),
            mock_session,
            mock_user,
        )

    assert exc.value.status_code == 404
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_dialogue_entry_text_success(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    await update_dialogue_entry_text(
        mock_transcription.id,
        0,
        UpdateDialogueEntryTextRequest(
            new_text="Updated hello",
            expected_text="Hello",
            expected_speaker="Alice",
            expected_start_time=0.0,
            expected_end_time=1.0,
        ),
        mock_session,
        mock_user,
    )

    assert mock_transcription.dialogue_entries == [
        {"speaker": "Alice", "text": "Updated hello", "start_time": 0.0, "end_time": 1.0},
        {"speaker": "Bob", "text": "Hi there", "start_time": 1.0, "end_time": 2.0},
    ]
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_dialogue_entry_text_conflict(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    with pytest.raises(HTTPException) as exc:
        await update_dialogue_entry_text(
            mock_transcription.id,
            0,
            UpdateDialogueEntryTextRequest(
                new_text="Updated hello",
                expected_text="Goodbye",
            ),
            mock_session,
            mock_user,
        )

    assert exc.value.status_code == 409
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("entry_index", [-1, 99])
async def test_update_dialogue_entry_text_not_found(mock_session, mock_user, mock_transcription, entry_index):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    with pytest.raises(HTTPException) as exc:
        await update_dialogue_entry_text(
            mock_transcription.id,
            entry_index,
            UpdateDialogueEntryTextRequest(new_text="Updated hello"),
            mock_session,
            mock_user,
        )

    assert exc.value.status_code == 404
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_labelled_transcriptions(mock_session, mock_user, mock_transcription):
    mock_session.exec = AsyncMock()
    mock_session.exec.side_effect = [Mock(one=Mock(return_value=1)), Mock(all=Mock(return_value=[mock_transcription]))]
    mock_transcription.dialogue_entries = [{"speaker": "Alice", "text": "Hello", "start_time": 0.0, "end_time": 1.0}]
    mock_transcription.status = JobStatus.COMPLETED
    mock_transcription.title = "Test Title"
    mock_transcription.date_of_recording = datetime(year=2021, month=1, day=1, tzinfo=UTC)

    result = await list_labelled_transcriptions(mock_session, mock_user, page=1, page_size=20)
    assert result.total_count == 1
    assert result.items[0].title == mock_transcription.title
    assert result.items[0].status == mock_transcription.status
    assert result.total_pages == 1
    assert result.items[0].created_datetime == mock_transcription.created_datetime
    assert result.items[0].date_of_recording == mock_transcription.date_of_recording


@pytest.mark.asyncio
async def test_list_unlabelled_transcriptions(mock_session, mock_user, mock_unlabelled_transcription):
    mock_session.exec = AsyncMock()
    mock_session.exec.side_effect = [
        Mock(one=Mock(return_value=1)),
        Mock(all=Mock(return_value=[mock_unlabelled_transcription])),
    ]
    mock_unlabelled_transcription.dialogue_entries = [
        {"speaker": "Alice", "text": "Hello", "start_time": 0.0, "end_time": 1.0}
    ]
    mock_unlabelled_transcription.status = JobStatus.COMPLETED
    mock_unlabelled_transcription.title = "Test Title"

    result = await list_unlabelled_transcriptions(mock_session, mock_user)
    assert result.total_count == 1
    assert result.items[0].title == mock_unlabelled_transcription.title
    assert result.items[0].status == mock_unlabelled_transcription.status
    assert result.items[0].date_of_recording == mock_unlabelled_transcription.date_of_recording


@pytest.mark.asyncio
async def test_get_transcription_success(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)
    mock_session.exec = AsyncMock(return_value=Mock(all=Mock(return_value=[datetime.now(UTC)])))
    response = await get_transcription(mock_transcription.id, mock_session, mock_user)
    assert response.id == mock_transcription.id
    assert response.title == mock_transcription.title
    assert response.is_upload is True


@pytest.mark.asyncio
async def test_get_transcription_sets_is_upload_false_when_file_created_at_missing(
    mock_session, mock_user, mock_transcription
):
    mock_session.get = AsyncMock(return_value=mock_transcription)
    mock_session.exec = AsyncMock(return_value=Mock(all=Mock(return_value=[None])))

    response = await get_transcription(mock_transcription.id, mock_session, mock_user)

    assert response.is_upload is False


@pytest.mark.asyncio
async def test_get_transcription_not_found(mock_session, mock_user):
    mock_session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await get_transcription(uuid.uuid4(), mock_session, mock_user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_transcription(mock_session, mock_user, mock_transcription):
    mock_session.get = AsyncMock(return_value=mock_transcription)

    await delete_transcription(mock_transcription.id, mock_session, mock_user)

    mock_session.delete.assert_awaited_once_with(mock_transcription)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_transcription_not_found(mock_session, mock_user):
    mock_session.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await delete_transcription(uuid.uuid4(), mock_session, mock_user)
    assert exc.value.status_code == 404
