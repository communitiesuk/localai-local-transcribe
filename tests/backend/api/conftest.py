import datetime
import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from common.types import RecordingCreateRequest, TranscriptionCreateRequest, TranscriptionPatchRequest

# Various pytest fixtures for the backend module.


@pytest.fixture
def mock_user():
    user = Mock()
    user.email = "test@local-transcribe.com"
    user.id = 1
    return user


@pytest.fixture
def mock_storage_service(mocker):
    service = mocker.patch("backend.api.routes.transcriptions.storage_service")
    service.check_object_exists = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_transcription_queue_service(mocker):
    service = mocker.patch("backend.api.routes.transcriptions.transcription_queue_service")
    service.publish_message = Mock()
    return service


@pytest.fixture
def transcription_request():
    return TranscriptionCreateRequest(
        recording_id=uuid.uuid4(),
        title="Test Transcription",
        template_name="default",
        template_id=None,
        agenda=None,
    )


@pytest.fixture
def mock_session(mocker):
    session = mocker.AsyncMock()
    session.add = mocker.Mock()
    session.commit = AsyncMock()
    session.get = AsyncMock()
    return session


@pytest.fixture
def mock_recording():
    recording = Mock()
    recording.id = uuid.uuid4()
    recording.user_id = 1
    recording.s3_file_key = "audio/file.mp3"
    recording.transcription_id = None
    return recording


@pytest.fixture
def mock_session_with_recording(mock_session, mock_recording):
    mock_session.get.return_value = mock_recording
    return mock_session


@pytest.fixture
def mock_storage_service_recording(mocker):
    """Storage service mock for recording tests"""
    service = mocker.patch("backend.api.routes.transcriptions.storage_service")
    service.generate_presigned_url_put_object = AsyncMock(return_value="https://example.s3.amazonaws.com/put-123")

    service.generate_presigned_url_get_object = AsyncMock(return_value="https://example.s3.amazonaws.com/get-123")

    service.check_object_exists = AsyncMock(return_value=True)
    return service


@pytest.fixture
def recording_create_request():
    """Fixture for RecordingCreateRequest"""
    return RecordingCreateRequest(file_extension="mp3")


@pytest.fixture
def mock_transcription():
    """Fixture for a mock Transcription object"""
    transcription = Mock()
    transcription.id = uuid.uuid4()
    transcription.user_id = 1
    transcription.status = "completed"
    transcription.dialogue_entries = [
        {"speaker": "Alice", "text": "Hello", "start_time": 0.0, "end_time": 1.0},
        {"speaker": "Bob", "text": "Hi there", "start_time": 1.0, "end_time": 2.0},
    ]
    transcription.title = "Test Transcription"
    transcription.created_datetime = datetime.datetime(2024, 1, 15, 10, 30, 0, tzinfo=datetime.UTC)
    return transcription


@pytest.fixture
def transcription_patch_request():
    """Fixture for TranscriptionPatchRequest"""
    return TranscriptionPatchRequest(
        title="Mocked Transcription Title",
        dialogue_entries=[
            {"speaker": "Alice", "text": "Updated dialogue 1", "start_time": 0.0, "end_time": 5.5},
            {"speaker": "Bob", "text": "Updated dialogue 2", "start_time": 5.5, "end_time": 12.3},
        ],
    )
