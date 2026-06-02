from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from backend.api.dependencies.get_session import SQLSessionDep
from backend.api.dependencies.get_current_user import UserDep
from common.database.postgres_models import Organisation


async def get_organisation(
    user: UserDep,
    session: SQLSessionDep,
) -> Organisation:
    organisation = await session.get(Organisation, user.organisation_id)
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    return organisation


OrganisationDep = Annotated[Organisation, Depends(get_organisation)]
