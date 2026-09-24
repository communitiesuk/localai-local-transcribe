import logging
from datetime import UTC, datetime
from uuid import UUID

import sentry_sdk
from fastapi import APIRouter, HTTPException, Query
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError

from backend.api.dependencies import (
    OrganisationAdminDep,
    PendingTouUserDep,
    SQLSessionDep,
    TargetUserDep,
    UserDep,
)
from backend.services.emails import EmailSendError, get_email_sender
from backend.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from backend.utils.mappers import to_user_response
from backend.utils.queries import get_paginated_users, get_user_by_email, get_user_by_evaluation_id
from common.auth import is_admin_for_org, is_system_admin
from common.database.postgres_models import AnalyticsEventType, Organisation, User, UserRole
from common.services.analytics_service import record_analytics_event
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

email_sender = get_email_sender()

EVALUATION_ID_UNIQUE_CONSTRAINT = "uq_user_evaluation_id"
EVALUATION_ID_IN_USE_DETAIL = "This evaluation ID is already in use."


@users_router.get("/me")
def get_user(user: PendingTouUserDep) -> GetUserResponse:
    return to_user_response(user)


@users_router.post("/terms-of-use")
async def accept_terms_of_use(
    user: PendingTouUserDep,
    session: SQLSessionDep,
) -> GetUserResponse:
    user.accepted_tou = True

    await session.commit()
    await session.refresh(user)

    return to_user_response(user)


@users_router.get("/me/organisation")
async def get_organisation_name(user: UserDep, session: SQLSessionDep) -> str:
    if not user.organisation_id:
        raise HTTPException(status_code=404, detail="Organisation not found")

    organisation = await session.get(Organisation, user.organisation_id)
    if organisation is None:
        raise HTTPException(status_code=404, detail="Organisation not found")

    return organisation.name


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

    is_existing_evaluation_id = await get_user_by_evaluation_id(session, data.evaluation_id)
    if is_existing_evaluation_id:
        # The evaluation ID is never echoed back, so it stays out of the detail.
        raise HTTPException(status_code=409, detail=EVALUATION_ID_IN_USE_DETAIL)

    email_domain = data.email.split("@")[1]
    lowered_allowed_domains = [domain.lower() for domain in organisation.allowed_domains]
    if email_domain not in lowered_allowed_domains:
        raise HTTPException(
            status_code=400, detail=f"An email of domain '{email_domain}' is not associated with this organisation"
        )

    new_user = User(
        name=data.name,
        email=data.email,
        evaluation_id=data.evaluation_id,
        organisation_id=organisation.id,
    )

    session.add(new_user)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        # A concurrent request may have taken the evaluation ID between the check above and the commit.
        if EVALUATION_ID_UNIQUE_CONSTRAINT in str(error.orig):
            raise HTTPException(status_code=409, detail=EVALUATION_ID_IN_USE_DETAIL) from error
        raise
    await session.refresh(new_user)

    try:
        org_name = None if is_system_admin(user) else organisation.name
        email_sender.send_invite_email(data.email, data.name, org_name)
    except EmailSendError as e:
        sentry_sdk.capture_exception(e)
    
    await record_analytics_event(
        session, AnalyticsEventType.USER_INVITED, new_user.evaluation_id, new_user.organisation_id
    )

    return to_user_response(new_user)


@users_router.get("")
async def list_users(
    admin: OrganisationAdminDep,
    session: SQLSessionDep,
    page: int = Query(DEFAULT_PAGE, ge=DEFAULT_PAGE),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> PaginatedUsersResponse:
    if is_system_admin(admin):
        return await get_paginated_users(session, None, page, page_size)

    organisation = await session.get(Organisation, admin.organisation_id)
    return await get_paginated_users(session, organisation, page, page_size)


@users_router.get("/{user_id}")
async def get_target_user(user: UserDep, target_user: TargetUserDep, session: SQLSessionDep) -> GetUserResponse:
    if is_system_admin(user):
        return to_user_response(target_user)

    if not target_user.organisation_id:
        raise HTTPException(status_code=404, detail="Resource not found")

    organisation = await session.get(Organisation, target_user.organisation_id)
    if not organisation or not is_admin_for_org(user, organisation):
        raise HTTPException(status_code=404, detail="Resource not found")

    return to_user_response(target_user)


@users_router.patch("/{user_id}/roles")
async def update_user_roles(
    data: UserUpdateRoles, target_user: TargetUserDep, session: SQLSessionDep, user: UserDep
) -> GetUserResponse:
    is_promoting_to_system_admin = UserRole.MHCLG_SUPPORT_ADMIN in data.roles and not is_system_admin(target_user)
    if is_promoting_to_system_admin:
        raise HTTPException(
            status_code=403,
            detail="MHCLG support admin role cannot be assigned this way",
        )

    involves_system_admin_role = UserRole.MHCLG_SUPPORT_ADMIN in data.roles or is_system_admin(target_user)

    if not is_system_admin(user):
        if involves_system_admin_role:
            raise HTTPException(
                status_code=403,
                detail="Only a system admin can perform this action",
            )

        if not target_user.organisation_id:
            raise HTTPException(status_code=404, detail="User not found")

        organisation = await session.get(Organisation, target_user.organisation_id)
        if not organisation:
            raise HTTPException(status_code=404, detail="Organisation not found")

        if not is_admin_for_org(user, organisation):
            raise HTTPException(status_code=404, detail="User not found")

    target_user.roles = data.roles

    session.add(target_user)
    await session.commit()
    await session.refresh(target_user)

    return to_user_response(target_user)


@users_router.delete("/{user_id}", status_code=204)
async def delete_user(session: SQLSessionDep, user: UserDep, target_user: TargetUserDep) -> None:
    if not is_system_admin(user):
        if is_system_admin(target_user):
            raise HTTPException(status_code=403, detail="Only a system admin can perform this action")

        if not target_user.organisation_id:
            raise HTTPException(status_code=404, detail="User not found")

        organisation = await session.get(Organisation, target_user.organisation_id)
        if not organisation:
            raise HTTPException(status_code=404, detail="Organisation not found")

        if not is_admin_for_org(user, organisation):
            raise HTTPException(status_code=404, detail="User not found")

    deleted_user_evaluation_id = target_user.evaluation_id
    deleted_user_organisation_id = target_user.organisation_id

    await session.delete(target_user)
    await session.commit()

    await record_analytics_event(
        session, AnalyticsEventType.USER_DELETED, deleted_user_evaluation_id, deleted_user_organisation_id
    )


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
