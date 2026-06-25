# ruff: noqa: ARG001
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from common.database.postgres_models import Organisation, UserRole
from tests.utils import get_test_client


@pytest_asyncio.fixture
async def client():
    async with get_test_client() as ac:
        yield ac


@pytest.mark.asyncio
async def test_non_admin_cannot_list_organisations(client, override_user):
    response = await client.get("/organisations")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this resource"


@pytest.mark.asyncio
async def test_admin_can_list_organisations(client, override_user, mock_user):
    mock_user.roles = [UserRole.MHCLG_SUPPORT_ADMIN]

    response = await client.get("/organisations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_organisation(client, mock_user, mock_session, override_session, override_user):
    mock_user.roles = [UserRole.MHCLG_SUPPORT_ADMIN]

    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    fixed_time = datetime.now(UTC)

    async def fake_refresh(obj):
        obj.created_datetime = fixed_time
        obj.updated_datetime = fixed_time

    mock_session.refresh.side_effect = fake_refresh

    payload = {
        "name": "Test Organisation",
        "allowed_domains": ["gov.uk"],
    }

    response = await client.post(
        "/organisations",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == payload["name"]
    assert data["allowed_domains"] == payload["allowed_domains"]

    mock_session.exec.assert_awaited_once()
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_duplicate_organisation(
    client,
    override_user,
    override_session,
    mock_user,
    mock_session,
):
    mock_user.roles = [UserRole.MHCLG_SUPPORT_ADMIN]

    existing_org = Organisation(
        id=uuid.uuid4(),
        name="Pre-existing Org",
        allowed_domains=["gov.uk"],
    )

    mock_result = Mock()
    mock_result.first.return_value = existing_org
    mock_session.exec.return_value = mock_result

    payload = {
        "name": "Pre-existing Org",
        "allowed_domains": ["gov.uk", "new.gov.uk"],
    }

    response = await client.post("/organisations", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Organisation with this name already exists"

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_organisation(
    client,
    override_user,
    override_session,
    mock_user,
    mock_session,
):
    mock_user.roles = [UserRole.MHCLG_SUPPORT_ADMIN]

    fixed_time = datetime.now(UTC)

    org = Organisation(
        id=uuid.uuid4(),
        name="Minute",
        allowed_domains=["gov.uk"],
        created_datetime=fixed_time,
        updated_datetime=fixed_time,
    )

    mock_session.get.return_value = org

    response = await client.delete(
        f"/organisations/{org.id}",
    )

    assert response.status_code == 204

    mock_session.delete.assert_awaited_once_with(org)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_organisation_not_found(
    client,
    override_user,
    mock_user,
    mock_session,
    override_session,
):
    mock_user.roles = [UserRole.MHCLG_SUPPORT_ADMIN]

    organisation_id = uuid.uuid4()

    mock_session.get = AsyncMock(return_value=None)

    response = await client.delete(f"/organisations/{organisation_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Organisation not found"

    mock_session.get.assert_awaited_once_with(Organisation, organisation_id)

    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_organisations_domains(
    client,
    override_user,
    override_session,
    mock_user,
    mock_session,
):
    mock_user.roles = [UserRole.MHCLG_SUPPORT_ADMIN]
    time_now = datetime.now(UTC)
    new_domains = ["new.gov.uk", "updated.gov.uk"]

    org = Organisation(
        id=uuid.uuid4(),
        name="Test Organisation",
        allowed_domains=["old.gov.uk"],
        created_datetime=time_now,
        updated_datetime=time_now,
    )

    mock_session.get.return_value = org

    response = await client.patch(
        f"/organisations/{org.id}",
        json={"allowed_domains": new_domains},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["allowed_domains"] == new_domains

    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(org)


@pytest.mark.asyncio
async def test_update_organisation_not_found(
    client,
    override_user,
    override_session,
    mock_user,
    mock_session,
):
    mock_user.roles = [UserRole.MHCLG_SUPPORT_ADMIN]

    organisation_id = uuid.uuid4()

    mock_session.get.return_value = None

    response = await client.patch(
        f"/organisations/{organisation_id}",
        json={"allowed_domains": ["updated.gov.uk"]},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Organisation not found"

    mock_session.commit.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_non_admin_cannot_list_organisation_users(
    client,
    override_user,
    override_session,
    mock_session,
):
    organisation_id = uuid.uuid4()

    response = await client.get(f"/organisations/{organisation_id}/users")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this resource"


@pytest.mark.asyncio
async def test_admin_can_list_organisation_users(
    client,
    override_user,
    override_session,
    mock_user,
    mock_session,
    make_organisation,
    make_user,
):
    mock_user.roles = [UserRole.MHCLG_SUPPORT_ADMIN]

    organisation = make_organisation()
    organisation.id = uuid.uuid4()

    user1 = make_user(organisation_id=organisation.id)
    user2 = make_user(organisation_id=organisation.id)

    mock_session.get.return_value = organisation

    mock_result = Mock()
    mock_result.one.return_value = 2
    mock_result.all.return_value = [user1, user2]
    mock_session.exec.return_value = mock_result

    response = await client.get(f"/organisations/{organisation.id}/users")

    assert response.status_code == 200

    data = response.json()
    assert data["total_count"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 1
    assert isinstance(data["items"], list)
    assert {item["id"] for item in data["items"]} == {str(user1.id), str(user2.id)}


@pytest.mark.asyncio
async def test_list_organisation_users_organisation_not_found(
    client,
    override_user,
    override_session,
    mock_user,
    mock_session,
):
    mock_user.roles = [UserRole.MHCLG_SUPPORT_ADMIN]

    organisation_id = uuid.uuid4()
    mock_session.get.return_value = None

    response = await client.get(f"/organisations/{organisation_id}/users")

    assert response.status_code == 404
    assert response.json()["detail"] == "Organisation not found"

    mock_session.exec.assert_not_awaited()
