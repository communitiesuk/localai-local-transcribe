from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from backend.api.dependencies.get_current_user import get_current_user
from backend.api.dependencies.get_session import get_session
from backend.main import app
from common.database.postgres_models import (
    Chat,
    ContentSource,
    JobStatus,
    Minute,
    MinuteVersion,
    Organisation,
    Recording,
    TemplateType,
    Transcription,
    User,
    UserRole,
    UserTemplate,
)
from common.types import (
    Question,
    RecordingCreateRequest,
    TranscriptionCreateRequest,
    TranscriptionPatchRequest,
)

mock_email = "test@local-transcribe.com"


@pytest.fixture
def mock_user() -> User:
    return User(
        id=uuid4(),
        email=mock_email,
        data_retention_days=30,
        created_datetime=datetime.now(UTC),
        updated_datetime=datetime.now(UTC),
        roles=[UserRole.STANDARD_USER],
    )


@pytest.fixture
def override_user(mock_user):
    async def _override():
        return mock_user

    app.dependency_overrides[get_current_user] = _override
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def make_user():
    def _make_user(
        organisation_id=None,
        roles=None,
    ):
        return User(
            id=uuid4(),
            email=mock_email,
            organisation_id=organisation_id or uuid4(),
            roles=roles or [UserRole.STANDARD_USER],
            data_retention_days=30,
            created_datetime=datetime.now(UTC),
            updated_datetime=datetime.now(UTC),
        )

    return _make_user


@pytest.fixture
def make_organisation():
    def _make_organisation(
        name: str | None = None,
        allowed_domains: list[str] | None = None,
    ):
        return Organisation(
            name=name or f"org-{uuid4()}",
            allowed_domains=allowed_domains or [],
        )

    return _make_organisation


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
def override_session(mock_session):
    async def _override():
        return mock_session

    app.dependency_overrides[get_session] = _override
    yield mock_session
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def mock_recording(mock_user):
    recording = Mock(spec=Recording)
    recording.id = uuid4()
    recording.user_id = mock_user.id
    recording.s3_file_key = "audio/file.mp3"
    recording.transcription_id = None
    return recording


@pytest.fixture
def mock_session_with_recording(mock_session, mock_recording):
    mock_session.get.return_value = mock_recording
    return mock_session


@pytest.fixture
def recording_create_request():
    return RecordingCreateRequest(file_extension="mp3")


@pytest.fixture
def mock_minute() -> Minute:
    return Minute(
        id=uuid4(),
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        transcription_id=uuid4(),
        template_name="TEMPLATE",
        user_template_id=None,
        agenda="AGENDA",
        minute_versions=[],
    )


@pytest.fixture
def mock_minute_version(mock_minute) -> MinuteVersion:
    return MinuteVersion(
        id=uuid4(),
        minute_id=mock_minute.id,
        minute=mock_minute,
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        ai_edit_instructions=None,
        html_content="<p>hello world</p>",
        content_source=ContentSource.INITIAL_GENERATION,
    )


@pytest.fixture
def mock_transcription(mock_minute, mock_user) -> Transcription:
    return Transcription(
        id=uuid4(),
        user_id=mock_user.id,
        audio_url="https://example.com/audio.mp3",
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        minutes=[mock_minute],
        title="Test Transcription",
        dialogue_entries=[
            {"speaker": "Alice", "text": "Hello", "start_time": 0.0, "end_time": 1.0},
            {"speaker": "Bob", "text": "Hi there", "start_time": 1.0, "end_time": 2.0},
        ],
    )


@pytest.fixture
def transcription_request():
    return TranscriptionCreateRequest(
        recording_id=uuid4(),
        title="Test Transcription",
        template_name="default",
        template_id=None,
        agenda=None,
    )


@pytest.fixture
def transcription_patch_request():
    return TranscriptionPatchRequest(
        title="Mocked Transcription Title",
        dialogue_entries=[
            {"speaker": "Alice", "text": "Updated dialogue 1", "start_time": 0.0, "end_time": 5.5},
            {"speaker": "Bob", "text": "Updated dialogue 2", "start_time": 5.5, "end_time": 12.3},
        ],
    )


@pytest.fixture
def mock_storage_service(mocker):
    service = mocker.patch("backend.api.routes.transcriptions.storage_service")
    service.check_object_exists = AsyncMock(return_value=True)
    service.generate_presigned_url_put_object = AsyncMock(return_value="https://example.s3.amazonaws.com/put-123")
    service.generate_presigned_url_get_object = AsyncMock(return_value="https://example.s3.amazonaws.com/get-123")
    return service


@pytest.fixture
def mock_transcription_queue_service(mocker):
    service = mocker.patch("backend.api.routes.transcriptions.transcription_queue_service")
    service.publish_message = Mock()
    return service


@pytest.fixture
def patch_llm_queue_service(monkeypatch):
    mock_queue = Mock()
    monkeypatch.setattr("backend.api.routes.chat.llm_queue_service", mock_queue)
    return mock_queue


@pytest.fixture
def mock_chat(uid=None, user_content="hello", assistant_content="world", status="completed") -> Chat:
    return Chat(
        id=uid or uuid4(),
        user_content=user_content,
        assistant_content=assistant_content,
        status=status,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
    )


@pytest.fixture
def mock_user_template(mock_user) -> UserTemplate:
    return UserTemplate(
        id=uuid4(),
        user_id=mock_user.id,
        name="Test Template",
        description="Test Description",
        content="Hello World",
        type=TemplateType.DOCUMENT,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        minutes=[],
        questions=[],
    )


@pytest.fixture
def mock_request():
    return SimpleNamespace(
        name="Test Template",
        content="Hello World",
        description="test template",
        type=TemplateType.DOCUMENT,
        questions=[Question(id=uuid4(), position=1, title="Foo", description="foobar")],
    )
