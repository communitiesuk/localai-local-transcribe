from typing import Annotated

from fastapi import Depends, HTTPException

from backend.api.dependencies.get_current_user import UserDep
from backend.api.dependencies.get_session import SQLSessionDep
from common.auth import is_admin_for_org, is_system_admin
from common.database.postgres_models import Organisation, User


async def get_org_admin(user: UserDep, session: SQLSessionDep) -> User:
    if is_system_admin(user):
        return user

    if not user.organisation_id:
        raise HTTPException(status_code=403, detail="User not in organisation")

    organisation = await session.get(Organisation, user.organisation_id)
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not is_admin_for_org(user, organisation):
        raise HTTPException(
            status_code=403,
            detail="Only an organisation admin can perform this action",
        )

    return user


OrganisationAdminDep = Annotated[User, Depends(get_org_admin)]
