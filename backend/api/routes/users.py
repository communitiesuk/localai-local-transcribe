import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from backend.api.dependencies import (
    OrganisationAdminDep,
    SQLSessionDep,
    SystemAdminDep,
    TargetUserDep,
    UserDep,
)
from backend.utils.mappers import to_user_response
from backend.utils.queries import get_users, organisation_from_id
from common.auth import is_admin_for_org
from common.database.postgres_models import User
from common.types import DataRetentionUpdateResponse, GetUserResponse, UserCreate, UserUpdateRoles

users_router = APIRouter(prefix="/users", tags=["Users"])
org_users_router = APIRouter(prefix="/orgs/{organisation_id}/users", tags=["Users"])

logger = logging.getLogger(__name__)


@users_router.get("/me")
def get_user(user: UserDep) -> GetUserResponse:
    return to_user_response(user)


@users_router.patch("/data-retention", response_model=GetUserResponse)
async def update_data_retention(
    data: DataRetentionUpdateResponse,
    session: SQLSessionDep,
    user: UserDep,
) -> GetUserResponse:
    """Update the data retention period for the current user.

    Args:
        data: Request body containing data_retention_days
        current_user: The current authenticated user
    """
    if data.data_retention_days is not None and data.data_retention_days < 1:
        raise HTTPException(
            status_code=400,
            detail="Data retention period must be at least 1 day or None for indefinite retention",
        )

    user.data_retention_days = data.data_retention_days
    user.updated_datetime = datetime.now(tz=UTC)

    await session.commit()
    await session.refresh(user)

    logger.info(
        "Updated data retention period to %s days for user %s",
        data.data_retention_days,
        user.id,
    )

    return to_user_response(user)


@users_router.post("")
async def create_user(
    data: UserCreate,
    session: SQLSessionDep,
    user: UserDep,
) -> GetUserResponse:
    organisation = await organisation_from_id(session, data.organisation_id)
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, organisation):
        raise HTTPException(status_code=403, detail="Only an organisation admin can create a new user")

    email_domain = data.email.split("@")[1]
    if email_domain not in organisation.allowed_domains:
        raise HTTPException(
            status_code=400, detail=f"An email of domain '{email_domain}' is not associated with this organisation"
        )

    new_user = User(email=data.email, organisation_id=organisation.id)

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return to_user_response(new_user)


@users_router.get("")
async def list_users(
    _: SystemAdminDep,
    session: SQLSessionDep,
) -> list[GetUserResponse]:
    users = await get_users(session)
    return [to_user_response(user) for user in users]


@users_router.get("/{user_id}")
async def list_user(
    _: SystemAdminDep,
    target_user: TargetUserDep,
) -> GetUserResponse:
    return to_user_response(target_user)


@org_users_router.get("")
async def list_users_in_org(
    organisation: OrganisationAdminDep,
    session: SQLSessionDep,
) -> list[GetUserResponse]:
    users = await get_users(session, organisation)
    return [to_user_response(user) for user in users]


@org_users_router.get("/{user_id}")
async def list_user_in_org(_: OrganisationAdminDep, target_user: TargetUserDep) -> GetUserResponse:
    return to_user_response(target_user)


@users_router.patch("/{user_id}/roles")
async def update_user_roles(
    _: OrganisationAdminDep,
    data: UserUpdateRoles,
    target_user: TargetUserDep,
    session: SQLSessionDep,
) -> GetUserResponse:
    target_user.roles = data.roles

    session.add(target_user)

    await session.commit()
    await session.refresh(target_user)

    return to_user_response(target_user)


@users_router.delete("/{user_id}", status_code=204)
async def delete_user(session: SQLSessionDep, user: UserDep, target_user: TargetUserDep) -> None:
    if not target_user.organisation_id:
        raise HTTPException(status_code=404, detail="User not found within organisation")

    organisation = await organisation_from_id(session, target_user.organisation_id)
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, organisation):
        raise HTTPException(status_code=403, detail="Only an organisation admin can delete a user")

    await session.delete(target_user)
    await session.commit()
