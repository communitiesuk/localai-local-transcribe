# ruff: noqa: ARG001
# needed for pytest fixtures

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from backend.api.dependencies.get_current_user import get_current_user
from backend.api.dependencies.get_target_user import get_target_user
from backend.main import app
from backend.services.emails import EmailSendError
from common.database.postgres_models import AnalyticsEventType, UserRole
from tests.utils import get_test_client


def convert_to_datetime(json_datetime: str) -> datetime:
    return datetime.fromisoformat(json_datetime.replace("Z", "+00:00"))


async def user_create_refresh(user):
    user.id = uuid4()
    user.created_datetime = datetime.now(UTC)
    user.updated_datetime = datetime.now(UTC)
    user.last_login = datetime.now(UTC)


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


@pytest.mark.skip(reason="run test only after AIILG-764 implemented")
@pytest.mark.asyncio
async def test_accept_terms_of_use_success(override_user, override_session, mock_pending_tou_user, mock_session):
    assert mock_pending_tou_user.accepted_tou is False

    async with get_test_client() as ac:
        response = await ac.post("/users/terms-of-use")

    assert response.status_code == 200
    data = response.json()

    assert mock_pending_tou_user.accepted_tou is True
    assert data["id"] == str(mock_pending_tou_user.id)
    assert data["email"] == mock_pending_tou_user.email
    assert data["accepted_tou"] is True

    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(mock_pending_tou_user)


@pytest.mark.parametrize("retention_period", [1, 7, 30])
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

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_roles", "target_user_roles", "same_org", "new_roles", "expected_status"),
    [
        ([UserRole.MHCLG_SUPPORT_ADMIN], [UserRole.STANDARD_USER], True, [UserRole.MHCLG_SUPPORT_ADMIN], 403),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.STANDARD_USER], True, [UserRole.LOCAL_AUTHORITY_ADMIN], 200),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.STANDARD_USER], True, [UserRole.MHCLG_SUPPORT_ADMIN], 403),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.MHCLG_SUPPORT_ADMIN], True, [UserRole.STANDARD_USER], 403),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], [UserRole.STANDARD_USER], False, [UserRole.LOCAL_AUTHORITY_ADMIN], 404),
        ([UserRole.MHCLG_SUPPORT_ADMIN], [UserRole.MHCLG_SUPPORT_ADMIN], True, [UserRole.STANDARD_USER], 200),
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
async def test_delete_user_records_user_deleted_analytics_event(
    mocker,
    override_session,
    make_user,
    make_organisation,
):
    """Deleting a user records a USER_DELETED analytics event with the deleted user's evaluation_id."""
    organisation = make_organisation()
    override_session.get.return_value = organisation

    user = make_user(organisation_id=organisation.id, roles=[UserRole.MHCLG_SUPPORT_ADMIN])
    app.dependency_overrides[get_current_user] = lambda: user

    target_user = make_user(organisation_id=organisation.id, roles=[UserRole.STANDARD_USER])
    target_user.evaluation_id = "EVAL-DELETE"
    app.dependency_overrides[get_target_user] = lambda: target_user

    mock_record_event = mocker.patch("backend.api.routes.users.record_analytics_event", new=AsyncMock())

    async with get_test_client() as ac:
        response = await ac.delete(f"/users/{target_user.id}")

    assert response.status_code == 204
    mock_record_event.assert_awaited_once()
    call_args = mock_record_event.await_args
    assert call_args.args[0] is override_session
    assert call_args.args[1] == AnalyticsEventType.USER_DELETED
    assert call_args.args[2] == "EVAL-DELETE"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("admin_roles", "expected_inviter_organisation_name"),
    [
        ([UserRole.MHCLG_SUPPORT_ADMIN], None),
        ([UserRole.LOCAL_AUTHORITY_ADMIN], "Example Council"),
    ],
)
async def test_create_user(
    mocker,
    override_session,
    make_user,
    make_organisation,
    mock_email_sender,
    admin_roles,
    expected_inviter_organisation_name,
):
    """Creating a new user records a USER_INVITED analytics event and sends an invite email."""
    organisation = make_organisation(name="Example Council", allowed_domains=["example.gov.uk"])
    mock_session = override_session
    mock_session.get.return_value = organisation
    mock_session.refresh.side_effect = user_create_refresh

    user = make_user(organisation_id=organisation.id, roles=admin_roles)
    app.dependency_overrides[get_current_user] = lambda: user

    mock_record_event = mocker.patch("backend.api.routes.users.record_analytics_event", new=AsyncMock())

    with (
        patch(
            "backend.api.routes.users.get_user_by_email",
            new=AsyncMock(return_value=None),
        ),
        patch("backend.api.routes.users.get_user_by_evaluation_id", new=AsyncMock(return_value=None)),
    ):
        async with get_test_client() as ac:
            response = await ac.post(
                "/users",
                json={
                    "name": "Test User",
                    "email": "test.user@example.gov.uk",
                    "evaluation_id": "EVAL-001",
                    "organisation_id": str(organisation.id),
                },
            )

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test.user@example.gov.uk"
    assert data["organisation_id"] == str(organisation.id)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_email_sender.send_invite_email.assert_called_once_with(
        "test.user@example.gov.uk",
        "Test User",
        expected_inviter_organisation_name,
    )

    mock_record_event.assert_awaited_once()
    call_args = mock_record_event.await_args
    assert call_args.args[0] is override_session
    assert call_args.args[1] == AnalyticsEventType.USER_INVITED
    assert call_args.args[2] == "EVAL-001"


@pytest.mark.asyncio
async def test_create_user_email_failure_calls_sentry(
    mocker,
    override_session,
    override_support_admin_user,
    make_organisation,
    mock_email_sender,
):
    """The USER_INVITED analytics event is still recorded even if the invite email fails to send."""
    organisation = make_organisation(allowed_domains=["example.gov.uk"])
    mock_session = override_session
    mock_session.get.return_value = organisation
    mock_session.refresh.side_effect = user_create_refresh
    mock_email_sender.send_invite_email.side_effect = EmailSendError

    mock_record_event = mocker.patch("backend.api.routes.users.record_analytics_event", new=AsyncMock())

    with (
        patch("backend.api.routes.users.get_user_by_email", new=AsyncMock(return_value=None)),
        patch("backend.api.routes.users.get_user_by_evaluation_id", new=AsyncMock(return_value=None)),
        patch("backend.api.routes.users.sentry_sdk.capture_exception") as capture_exception,
    ):
        async with get_test_client() as ac:
            await ac.post(
                "/users",
                json={
                    "name": "Test User",
                    "email": "test.user@example.gov.uk",
                    "evaluation_id": "EVAL-001",
                    "organisation_id": str(organisation.id),
                },
            )

    capture_exception.assert_called_once()
    mock_record_event.assert_awaited_once()


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
                    "evaluation_id": "EVAL-001",
                    "roles": existing_user.roles,
                    "organisation_id": str(existing_user.organisation_id),
                },
            )

    assert response.json()["detail"] == f"A user with email '{existing_user.email}' already exists"
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_user_returns_409_when_evaluation_id_already_exists(
    override_session,
    override_support_admin_user,
    make_user,
):
    existing_user = make_user()
    existing_user.evaluation_id = "EVAL-001"

    with (
        patch(
            "backend.api.routes.users.get_user_by_email",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "backend.api.routes.users.get_user_by_evaluation_id",
            new=AsyncMock(return_value=existing_user),
        ),
    ):
        async with get_test_client() as ac:
            response = await ac.post(
                "/users",
                json={
                    "name": "Test User",
                    "email": "new.user@example.com",
                    "evaluation_id": existing_user.evaluation_id,
                    "organisation_id": str(existing_user.organisation_id),
                },
            )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "This evaluation ID is already in use. Check the evaluation ID you received from MHCLG."
    )
    assert existing_user.evaluation_id not in response.text


@pytest.mark.asyncio
async def test_create_user_rejects_a_missing_evaluation_id(
    override_session,
    override_support_admin_user,
    make_user,
):
    existing_user = make_user()

    async with get_test_client() as ac:
        response = await ac.post(
            "/users",
            json={
                "name": "Test User",
                "email": "new.user@example.com",
                "organisation_id": str(existing_user.organisation_id),
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_rejects_a_whitespace_only_evaluation_id(
    override_session,
    override_support_admin_user,
    make_user,
):
    existing_user = make_user()

    async with get_test_client() as ac:
        response = await ac.post(
            "/users",
            json={
                "name": "Test User",
                "email": "new.user@example.com",
                "evaluation_id": "   ",
                "organisation_id": str(existing_user.organisation_id),
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_returns_409_when_a_concurrent_request_takes_the_evaluation_id(
    override_session,
    override_support_admin_user,
    make_organisation,
):
    organisation = make_organisation(allowed_domains=["example.com"])
    override_session.get.return_value = organisation
    override_session.commit.side_effect = IntegrityError(
        "INSERT",
        {},
        Exception('duplicate key value violates unique constraint "uq_user_evaluation_id"'),
    )
    override_session.rollback = AsyncMock()

    with (
        patch("backend.api.routes.users.get_user_by_email", new=AsyncMock(return_value=None)),
        patch("backend.api.routes.users.get_user_by_evaluation_id", new=AsyncMock(return_value=None)),
    ):
        async with get_test_client() as ac:
            response = await ac.post(
                "/users",
                json={
                    "name": "Test User",
                    "email": "new.user@example.com",
                    "evaluation_id": "EVAL-001",
                    "organisation_id": str(organisation.id),
                },
            )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "This evaluation ID is already in use. Check the evaluation ID you received from MHCLG."
    )
    override_session.rollback.assert_awaited_once()


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
