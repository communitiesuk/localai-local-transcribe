import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException

from backend.api.dependencies import SQLSessionDep, UserDep
from backend.utils.database import organisation_from_id, user_from_id
from common.auth import is_admin_for_org
from common.database.postgres_models import User
from common.types import DataRetentionUpdateResponse, GetUserResponse, UserCreate

users_router = APIRouter(prefix="/users", tags=["Users"])

logger = logging.getLogger(__name__)


@users_router.get("/me")
def get_user(user: UserDep) -> GetUserResponse:
    return GetUserResponse(
        id=user.id,
        created_datetime=user.created_datetime,
        updated_datetime=user.updated_datetime,
        email=user.email,
        data_retention_days=user.data_retention_days,
    )


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

    return GetUserResponse(
        id=user.id,
        created_datetime=user.created_datetime,
        updated_datetime=user.updated_datetime,
        email=user.email,
        data_retention_days=user.data_retention_days,
    )


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

    return GetUserResponse(
        id=new_user.id,
        created_datetime=new_user.created_datetime,
        updated_datetime=new_user.updated_datetime,
        email=new_user.email,
        data_retention_days=new_user.data_retention_days,
    )


@users_router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: UUID, session: SQLSessionDep, user: UserDep) -> None:
    target_user = await user_from_id(session, user_id)
    if not target_user or not target_user.organisation_id:
        raise HTTPException(status_code=400, detail="User not found within organisation")

    organisation = await organisation_from_id(session, target_user.organisation_id)
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, organisation):
        raise HTTPException(status_code=403, detail="Only an organisation admin can delete a user")

    await session.delete(target_user)
    await session.commit()
