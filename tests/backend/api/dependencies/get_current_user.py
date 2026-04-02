from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from backend.api.dependencies.get_current_user import get_current_user
from common.services.exceptions import MissingAuthTokenError


@pytest.fixture
def session():
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.exec = AsyncMock()

    return session


@pytest.mark.asyncio
async def test_get_current_user_existing_user(monkeypatch, session):
    mock_user = Mock(email="test@example.com")
    mock_result = Mock()
    mock_result.first.return_value = mock_user
    session.exec.return_value = mock_result  # return mock user as a db result

    # patch in JWT decoding
    mock_auth_info = Mock(email="test@example.com", is_authorised=True)
    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        lambda _: mock_auth_info,  # token unused in test
    )

    user = await get_current_user(
        session=session,
        x_amzn_oidc_data="token",
    )

    # check emails match and no new user is created
    assert user == mock_user
    session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_creates_user(monkeypatch, session):
    mock_result = Mock()
    mock_result.first.return_value = None  # no user currently exists
    session.exec.return_value = mock_result

    mock_auth_info = Mock(email="test@example.com", is_authorised=True)
    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        lambda _: mock_auth_info,
    )

    user = await get_current_user(
        session=session,
        x_amzn_oidc_data="token",
    )

    assert user.email == mock_auth_info.email
    session.add.assert_called_once()  # new user created
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_user_unauthorised(monkeypatch, session):
    mock_auth_info = Mock(email="test@example.com", is_authorised=False)

    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        lambda _: mock_auth_info,  # not authorised so will raise first exception
    )

    with pytest.raises(HTTPException) as exception:
        await get_current_user(
            session=session,
            x_amzn_oidc_data="token",
        )

    assert exception.value.status_code == 401
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
