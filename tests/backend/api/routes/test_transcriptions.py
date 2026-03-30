import pytest
from fastapi import HTTPException
from backend.api.routes.transcriptions import create_transcription
from common.types import TranscriptionCreateRequest

@pytest.mark.asyncio
async def test_create_transcription_success(mocker):
    # Arrange
    mock_session = mocker.AsyncMock()
    mock_user = mocker.Mock()
    mock_user.id = 1
    mock_recording = mocker.Mock()
    mock_recording.user_id = 1
    mock_recording.s3_file_key = "audio/file.mp3"
    mock_session.get.return_value = mock_recording

    mock_storage_service = mocker.patch(
        "backend.api.routes.transcriptions.storage_service"
    )
    mock_storage_service.check_object_exists.return_value = True

    mock_transcription_queue_service = mocker.patch(
        "backend.api.routes.transcriptions.transcription_queue_service"
    )

    request = TranscriptionCreateRequest(
        recording_id=123,
        title="Test Transcription",
        template_name="default",
        template_id=None,
        agenda=None,
    )

    # Act
    response = await create_transcription(request, mock_session, mock_user)

    # Assert
    assert response.id is not None
    mock_session.add.assert_called()
    mock_session.commit.assert_awaited()
    mock_transcription_queue_service.publish_message.assert_called()