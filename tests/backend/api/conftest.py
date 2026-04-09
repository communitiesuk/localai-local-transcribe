import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from common.database.postgres_models import Chat, ContentSource, JobStatus, Minute, MinuteVersion, Transcription, User

make_email = "tests@local-transcribe.gov.uk"


@pytest.fixture
def make_user() -> User:
    return User(
        id=uuid.uuid4(),
        email=make_email,
    )


@pytest.fixture
def make_minute() -> Minute:
    return Minute(
        id=uuid.uuid4(),
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        transcription_id=uuid.uuid4(),
        template_name="TEMPLATE",
        user_template_id=None,
        agenda="AGENDA",
        minute_versions=[],
    )


@pytest.fixture
def make_minute_version(make_minute) -> MinuteVersion:
    return MinuteVersion(
        id=uuid.uuid4(),
        minute_id=make_minute.id,
        minute=make_minute,
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        ai_edit_instructions=None,
        html_content="<p>hello world</p>",
        content_source=ContentSource.INITIAL_GENERATION,
    )


@pytest.fixture
def make_transcription(make_minute) -> Transcription:
    return Transcription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        audio_url="https://example.com/audio.mp3",
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        minutes=[make_minute],
    )


@pytest.fixture
def mock_session():
    mock_session = AsyncMock()
    mock_session.exec = AsyncMock()
    mock_session.get = AsyncMock()
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.delete = AsyncMock()
    return mock_session


@pytest.fixture
def patch_llm_queue_service(monkeypatch):
    mock_queue = Mock()
    monkeypatch.setattr("backend.api.routes.chat.llm_queue_service", mock_queue)
    return mock_queue


@pytest.fixture
def make_chat(uid=None, user_content="hello", assistant_content="world", status="completed") -> Chat:
    return Chat(
        id=uid or uuid.uuid4(),
        user_content=user_content,
        assistant_content=assistant_content,
        status=status,
        created_datetime=datetime.now(UTC),
        updated_datetime=datetime.now(UTC),
    )

    