from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.api.dependencies.get_current_user import get_current_user
from common.database.postgres_models import User
from common.services.exceptions import MissingAuthTokenError

TEST_EMAIL = "test@local-transcribe.com"
TEST_TOKEN = "token"  # noqa: S105


@pytest.fixture
def session():
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.exec = AsyncMock()

    return session


def make_mock_get_user_info(email: str = TEST_EMAIL, is_authorised: bool = True):
    mock_auth_info = Mock(email=email, is_authorised=is_authorised)
    return Mock(return_value=mock_auth_info)


@pytest.mark.asyncio
async def test_get_current_user_existing_user(monkeypatch, session):
    mock_user = User(
        id=uuid4(),
        email=TEST_EMAIL,
        data_retention_days=30,
        created_datetime=datetime.now(UTC),
        updated_datetime=datetime.now(UTC),
    )
    mock_result = Mock()
    mock_result.first.return_value = mock_user
    session.exec.return_value = mock_result  # return mock user as a db result

    # patch in JWT decoding
    mock_get_user_info = make_mock_get_user_info()
    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        mock_get_user_info,  # token unused in test
    )

    user = await get_current_user(
        session=session,
        x_amzn_oidc_data=TEST_TOKEN,
    )

    # check emails match and no new user is created
    assert user.email == mock_user.email
    mock_get_user_info.assert_called_once_with(TEST_TOKEN)
    session.commit.assert_called_once()  # one call for subject_id


@pytest.mark.asyncio
async def test_get_current_user_creates_user(monkeypatch, session):
    mock_result = Mock()
    mock_result.first.return_value = None  # no user currently exists
    session.exec.return_value = mock_result

    new_user_email = "new_user_" + TEST_EMAIL
    mock_get_user_info = make_mock_get_user_info(email=new_user_email)
    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        mock_get_user_info,
    )

    user = await get_current_user(
        session=session,
        x_amzn_oidc_data=TEST_TOKEN,
    )

    assert user.email == new_user_email
    mock_get_user_info.assert_called_once_with(TEST_TOKEN)
    # new user is created, subject_id is added
    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_user_unauthorised(monkeypatch, session):
    mock_get_user_info = make_mock_get_user_info(is_authorised=False)
    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        mock_get_user_info,  # not authorised so will raise first exception
    )

    with pytest.raises(HTTPException) as exception:
        await get_current_user(
            session=session,
            x_amzn_oidc_data=TEST_TOKEN,
        )

    assert exception.value.status_code == 401
    mock_get_user_info.assert_called_once_with(TEST_TOKEN)
    session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_missing_token(monkeypatch, session):
    def mock_missing_auth_info(_):
        raise MissingAuthTokenError

    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        mock_missing_auth_info,
    )

    with pytest.raises(HTTPException) as exception:
        await get_current_user(
            session=session,
            x_amzn_oidc_data=None,
        )

    assert exception.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_unhandled_exception(monkeypatch, session):
    def mock_unexpected_error(_):
        msg = "unexpected"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        mock_unexpected_error,
    )

    with pytest.raises(HTTPException) as exception:
        await get_current_user(
            session=session,
            x_amzn_oidc_data=TEST_TOKEN,
        )

    assert exception.value.status_code == 500
