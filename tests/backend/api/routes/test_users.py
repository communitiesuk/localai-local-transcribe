# ruff: noqa: ARG001
# needed for pytest fixtures

from datetime import datetime

import pytest

from tests.utils import get_test_client


def convert_to_datetime(json_datetime: str) -> datetime:
    return datetime.fromisoformat(json_datetime.replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_get_user(override_user, mock_user):
    async with get_test_client() as ac:
        response = await ac.get("/users/me")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(mock_user.id)
    assert data["email"] == mock_user.email
    assert data["data_retention_days"] == mock_user.data_retention_days
    assert convert_to_datetime(data["created_datetime"]) == mock_user.created_datetime
    assert convert_to_datetime(data["updated_datetime"]) == mock_user.updated_datetime


@pytest.mark.parametrize("retention_period", [10, None])
@pytest.mark.asyncio
async def test_update_data_retention_success(
    override_user, override_session, mock_user, mock_session, retention_period
):
    assert mock_user.data_retention_days == 30  # confirm default retention period
    initial_updated_datetime = mock_user.updated_datetime

    async with get_test_client() as ac:
        response = await ac.patch(
            "/users/data-retention",
            json={"data_retention_days": retention_period},
        )

    assert response.status_code == 200
    data = response.json()

    # check retention data updated and returns updated user
    assert mock_user.data_retention_days == retention_period
    assert data["data_retention_days"] == retention_period
    assert convert_to_datetime(data["updated_datetime"]) != initial_updated_datetime

    # check db has been used
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(mock_user)


@pytest.mark.asyncio
async def test_update_data_retention_invalid(
    override_user,
    override_session,
):
    async with get_test_client() as ac:
        response = await ac.patch(
            "/users/data-retention",
            json={"data_retention_days": 0},
        )

    assert response.status_code == 400
    error_string = "Data retention period must be at least 1 day or None for indefinite retention"
    assert error_string == response.json()["detail"]
