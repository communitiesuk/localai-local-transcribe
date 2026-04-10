from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from backend.api.dependencies.get_current_user import get_current_user
from backend.api.dependencies.get_session import get_session
from backend.main import app
from common.database.postgres_models import (
    Chat, ContentSource, JobStatus, Minute, MinuteVersion, Transcription, User, UserTemplate
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
    )


@pytest.fixture
def override_user(mock_user):
    async def _override():
        return mock_user

    app.dependency_overrides[get_current_user] = _override
    yield
    app.dependency_overrides.pop(get_current_user, None)


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
    yield
    app.dependency_overrides.pop(get_session, None)


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
def mock_transcription(mock_minute) -> Transcription:
    return Transcription(
        id=uuid4(),
        user_id=uuid4(),
        audio_url="https://example.com/audio.mp3",
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        minutes=[mock_minute],
    )


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
        id=uuid.uuid4(),
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
   
