# ruff: noqa: ARG001
# needed for pytest fixtures

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from backend.api.dependencies.get_current_user import get_current_user
from backend.api.dependencies.get_target_user import get_target_user
from backend.main import app
from common.database.postgres_models import UserRole
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_roles", "target_user_roles", "same_org", "new_roles", "expected_status"),
    [
        ([UserRole.MHCLG_SUPPORT_ADMIN], [UserRole.STANDARD_USER], True, [UserRole.MHCLG_SUPPORT_ADMIN], 200),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.STANDARD_USER], True, [UserRole.LOCAL_AUTHORITY_ADMIN], 200),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.STANDARD_USER], True, [UserRole.MHCLG_SUPPORT_ADMIN], 403),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.MHCLG_SUPPORT_ADMIN], True, [UserRole.STANDARD_USER], 403),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.STANDARD_USER], False, [UserRole.LOCAL_AUTHORITY_ADMIN], 404),
    ],
)
async def test_update_user_roles(
    override_session, make_user, make_organisation, user_roles, target_user_roles, same_org, new_roles, expected_status
):
    organisation = make_organisation()

    async def fake_session_get_organisation_from_id(model, entry_id):
        return organisation if same_org else make_organisation()

    mock_session = override_session
    mock_session.get.side_effect = fake_session_get_organisation_from_id

    user = make_user(organisation_id=organisation.id, roles=user_roles)
    app.dependency_overrides[get_current_user] = lambda: user

    target_organisation_id = organisation.id if same_org else uuid4()
    target_user = make_user(organisation_id=target_organisation_id, roles=target_user_roles)
    app.dependency_overrides[get_target_user] = lambda: target_user

    async with get_test_client() as ac:
        response = await ac.patch(
            f"/users/{target_user.id}/roles",
            json={"roles": [r.value for r in new_roles]},
        )

    assert response.status_code == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_roles", "target_user_roles", "same_org", "expected_status"),
    [
        ([UserRole.MHCLG_SUPPORT_ADMIN], [UserRole.STANDARD_USER], True, 204),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.STANDARD_USER], True, 204),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.STANDARD_USER], False, 404),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.MHCLG_SUPPORT_ADMIN], True, 403),
    ],
)
async def test_delete_user(
    override_session, make_user, make_organisation, user_roles, same_org, target_user_roles, expected_status
):
    organisation = make_organisation()

    async def fake_session_get_organisation_from_id(model, entry_id):
        return organisation if same_org else make_organisation()

    mock_session = override_session
    mock_session.get.side_effect = fake_session_get_organisation_from_id

    user = make_user(organisation_id=organisation.id, roles=user_roles)
    app.dependency_overrides[get_current_user] = lambda: user

    target_organisation_id = organisation.id if same_org else uuid4()
    target_user = make_user(organisation_id=target_organisation_id, roles=target_user_roles)
    app.dependency_overrides[get_target_user] = lambda: target_user

    async with get_test_client() as ac:
        response = await ac.delete(f"/users/{target_user.id}")

    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_create_user_returns_409_when_email_already_exists(
    override_session,
    override_support_admin_user,
    make_user,
):
    existing_user = make_user()

    with patch(
        "backend.api.routes.users.get_user_by_email",
        new=AsyncMock(return_value=existing_user),
    ):
        async with get_test_client() as ac:
            response = await ac.post(
                "/users",
                json={
                    "name": "Test User",
                    "email": existing_user.email,
                    "roles": existing_user.roles,
                    "organisation_id": str(existing_user.organisation_id),
                },
            )

    assert response.json()["detail"] == f"A user with email '{existing_user.email}' already exists"
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_user_exists_returns_true_when_user_exists(
    override_session, override_support_admin_user, make_user, make_organisation
):
    existing_user = make_user()
    organisation = make_organisation()

    mock_session = override_session
    mock_session.get.return_value = organisation

    with patch(
        "backend.api.routes.users.get_user_by_email",
        new=AsyncMock(return_value=existing_user),
    ):
        async with get_test_client() as ac:
            response = await ac.get(f"/users/user/exists?email={existing_user.email}&organisation_id={organisation.id}")

    assert response.status_code == 200
    assert response.json() == {"exists": True}


@pytest.mark.asyncio
async def test_user_exists_returns_false_when_user_not_found(
    override_session, override_support_admin_user, make_organisation
):
    organisation = make_organisation()

    mock_session = override_session
    mock_session.get.return_value = organisation

    with patch(
        "backend.api.routes.users.get_user_by_email",
        new=AsyncMock(return_value=None),
    ):
        async with get_test_client() as ac:
            response = await ac.get(f"/users/user/exists?email=notfound@example.com&organisation_id={organisation.id}")

    assert response.status_code == 200
    assert response.json() == {"exists": False}


@pytest.mark.asyncio
async def test_user_exists_forbidden_for_non_admin(override_session, override_user, make_organisation):
    organisation = make_organisation()

    mock_session = override_session
    mock_session.get.return_value = organisation
    error_message = "Not authorized to access this resource"

    with patch(
        "backend.api.routes.users.get_user_by_email",
        new=AsyncMock(return_value=None),
    ):
        async with get_test_client() as ac:
            response = await ac.get(f"/users/user/exists?email=someone@example.com&organisation_id={organisation.id}")

    assert response.status_code == 403
    assert response.json()["detail"] == error_message


@pytest.mark.asyncio
async def test_user_exists_organisation_not_found(override_session, override_support_admin_user):
    mock_session = override_session
    mock_session.get.return_value = None
    error_message = "Organisation not found"

    with patch(
        "backend.api.routes.users.get_user_by_email",
        new=AsyncMock(return_value=None),
    ):
        async with get_test_client() as ac:
            response = await ac.get(f"/users/user/exists?email=someone@example.com&organisation_id={uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == error_message
