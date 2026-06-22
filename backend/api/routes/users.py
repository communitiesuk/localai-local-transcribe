import logging
import math
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import EmailStr

from backend.api.dependencies import (
    OrganisationAdminDep,
    SQLSessionDep,
    TargetUserDep,
    UserDep,
)
from backend.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from backend.utils.mappers import to_user_response
from backend.utils.queries import get_user_by_email, get_user_count, get_users
from common.auth import is_admin_for_org, is_system_admin
from common.database.postgres_models import Organisation, User, UserRole
from common.types import (
    DataRetentionUpdateResponse,
    GetUserResponse,
    PaginatedUsersResponse,
    UserCreate,
    UserExistsResponse,
    UserUpdateRoles,
)

users_router = APIRouter(prefix="/users", tags=["Users"])

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
    organisation = await session.get(Organisation, data.organisation_id)
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, organisation):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    is_existing_user = await get_user_by_email(session, data.email)
    if is_existing_user:
        raise HTTPException(status_code=409, detail=f"A user with email '{data.email}' already exists")

    email_domain = data.email.split("@")[1]
    lowered_allowed_domains = [domain.lower() for domain in organisation.allowed_domains]
    if email_domain not in lowered_allowed_domains:
        raise HTTPException(
            status_code=400, detail=f"An email of domain '{email_domain}' is not associated with this organisation"
        )

    new_user = User(name=data.name, email=data.email, organisation_id=organisation.id)

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return to_user_response(new_user)


@users_router.get("")
async def list_users(
    admin: OrganisationAdminDep,
    session: SQLSessionDep,
    page: int = Query(DEFAULT_PAGE, ge=DEFAULT_PAGE),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> PaginatedUsersResponse:
    users = []
    if is_system_admin(admin):
        count = await get_user_count(session)
        users = await get_users(
            session,
            page=page,
            page_size=page_size,
        )
    else:
        organisation = await session.get(Organisation, admin.organisation_id)
        count = await get_user_count(
            session,
            organisation=organisation,
        )
        users = await get_users(
            session,
            organisation=organisation,
            page=page,
            page_size=page_size,
        )

    return PaginatedUsersResponse(
        items=[to_user_response(u) for u in users],
        total_count=count,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(count / page_size) or 1,
    )


@users_router.get("/{user_id}")
async def get_target_user(user: UserDep, target_user: TargetUserDep, session: SQLSessionDep) -> GetUserResponse:
    if is_system_admin(user):
        return to_user_response(target_user)

    if not target_user.organisation_id:
        raise HTTPException(status_code=403, detail="Only an system admin can access this resource")

    organisation = await session.get(Organisation, target_user.organisation_id)
    if organisation is None:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, organisation):
        raise HTTPException(status_code=403, detail="Only an organisation admin can access this resource")

    return to_user_response(target_user)


@users_router.patch("/{user_id}/roles")
async def update_user_roles(
    data: UserUpdateRoles, target_user: TargetUserDep, session: SQLSessionDep, user: UserDep
) -> GetUserResponse:
    involves_system_admin_role = UserRole.MHCLG_SUPPORT_ADMIN in data.roles or is_system_admin(target_user)

    if is_system_admin(user):
        # system admins can update any user
        pass
    else:
        # only a system admin can grant/revoke system admin
        if involves_system_admin_role:
            raise HTTPException(
                status_code=403,
                detail="Only a system admin can perform this action",
            )

        if not target_user.organisation_id:
            raise HTTPException(status_code=404, detail="User not found")

        organisation = await session.get(
            Organisation,
            target_user.organisation_id,
        )
        if not organisation:
            raise HTTPException(
                status_code=404,
                detail="Organisation not found",
            )

        if not is_admin_for_org(user, organisation):
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

    target_user.roles = data.roles

    session.add(target_user)
    await session.commit()
    await session.refresh(target_user)

    return to_user_response(target_user)


@users_router.delete("/{user_id}", status_code=204)
async def delete_user(session: SQLSessionDep, user: UserDep, target_user: TargetUserDep) -> None:
    if is_system_admin(user):  # system admin can delete any user
        await session.delete(target_user)
        await session.commit()
        return

    if is_system_admin(target_user):
        raise HTTPException(status_code=403, detail="Only a system admin can perform this action")

    if not target_user.organisation_id:
        raise HTTPException(status_code=404, detail="User not found")

    organisation = await session.get(Organisation, target_user.organisation_id)
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, organisation):
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(target_user)
    await session.commit()


@users_router.get("/user/exists", response_model=UserExistsResponse)
async def user_exists(
    email: EmailStr,
    organisation_id: UUID,
    session: SQLSessionDep,
    user: UserDep,
) -> UserExistsResponse:
    organisation = await session.get(Organisation, organisation_id)
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, organisation):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

    existing_user = await get_user_by_email(session, email)

    return UserExistsResponse(exists=existing_user is not None)
