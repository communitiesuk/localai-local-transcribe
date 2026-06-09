from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.api.dependencies.get_current_user import get_current_user
from common.database.postgres_models import User
from common.services.exceptions import MissingAuthTokenError

TEST_EMAIL = "test@local-transcribe.com"
TEST_SUBJECT_ID = "sub_1234567890"
TEST_TOKEN = "token"  # noqa: S105


@pytest.fixture
def session():
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.exec = AsyncMock()

    return session


def make_mock_get_user_info(email: str = TEST_EMAIL, is_authorised: bool = True, subject_id: str = TEST_SUBJECT_ID):
    mock_auth_info = Mock(email=email, is_authorised=is_authorised, subject_id=subject_id)
    return Mock(return_value=mock_auth_info)


@pytest.mark.asyncio
async def test_get_current_user_existing_user(monkeypatch, session):
    mock_user = User(
        id=uuid4(),
        email=TEST_EMAIL,
        subject_id=TEST_SUBJECT_ID,
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
    session.commit.assert_not_called()

    # check the query filtered by subject_id
    executed_statement = session.exec.call_args.args[0]
    compiled = executed_statement.compile()
    assert "subject_id" in str(compiled)
    assert TEST_SUBJECT_ID in compiled.params.values()


@pytest.mark.asyncio
async def test_get_current_user_fallsback_to_email_if_no_subject_id(monkeypatch, session):
    mock_user = User(
        id=uuid4(),
        email=TEST_EMAIL,
        subject_id=None,
        data_retention_days=30,
        created_datetime=datetime.now(UTC),
        updated_datetime=datetime.now(UTC),
    )
    mock_result = Mock()
    # first returns no match, then returns the user
    # as the first query matches on subject id, and the second on email
    mock_result.first.side_effect = [None, mock_user]
    session.exec.return_value = mock_result

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

    # check emails match, and subject id has been populated
    assert user.email == mock_user.email
    assert user.subject_id == TEST_SUBJECT_ID
    mock_get_user_info.assert_called_once_with(TEST_TOKEN)
    session.commit.assert_awaited_once()

    # check the query filtered by email
    executed_statement = session.exec.call_args.args[0]
    compiled = executed_statement.compile()
    assert "email" in str(compiled)
    assert user.email in compiled.params.values()


@pytest.mark.asyncio
async def test_get_current_user_updates_email_of_existing_user(monkeypatch, session):
    mock_user = User(
        id=uuid4(),
        email=TEST_EMAIL,
        subject_id=TEST_SUBJECT_ID,
        data_retention_days=30,
        created_datetime=datetime.now(UTC),
        updated_datetime=datetime.now(UTC),
    )
    mock_result = Mock()
    mock_result.first.return_value = mock_user
    session.exec.return_value = mock_result  # return mock user as a db result

    new_email = "new_email"
    # patch in JWT decoding
    mock_get_user_info = make_mock_get_user_info(email=new_email)
    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        mock_get_user_info,  # token unused in test
    )

    user = await get_current_user(
        session=session,
        x_amzn_oidc_data=TEST_TOKEN,
    )

    # check emails match and is saved to the database
    assert user.email == new_email
    mock_get_user_info.assert_called_once_with(TEST_TOKEN)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_user_creates_user(monkeypatch, session):
    mock_result = Mock()
    mock_result.first.return_value = None  # no user currently exists
    session.exec.return_value = mock_result

    new_user_subject_id = "new_user_" + TEST_SUBJECT_ID
    mock_get_user_info = make_mock_get_user_info(subject_id=new_user_subject_id)
    monkeypatch.setattr(
        "backend.api.dependencies.get_current_user.get_user_info",
        mock_get_user_info,
    )

    user = await get_current_user(
        session=session,
        x_amzn_oidc_data=TEST_TOKEN,
    )

    assert user.subject_id == new_user_subject_id
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
