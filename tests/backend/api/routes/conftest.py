from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.api.dependencies.get_current_user import get_current_user
from backend.api.dependencies.get_session import get_session
from backend.main import app
from common.database.postgres_models import User


@pytest.fixture
def mock_user():
    return User(
        id=uuid4(),
        email="test@local-transcribe.com",
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
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def override_session(mock_session):
    async def _override():
        return mock_session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.pop(get_session, None)
