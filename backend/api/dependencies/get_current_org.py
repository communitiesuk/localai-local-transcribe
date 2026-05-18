from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import select

from backend.api.dependencies import SQLSessionDep, UserDep
from common.database.postgres_models import Organisation


async def get_current_org(session: SQLSessionDep, user: UserDep) -> Organisation:
    if not user.organisation_id:
        raise HTTPException(status_code=400, detail="User is not associated with an organisation")

    statement = select(Organisation).where(Organisation.id == user.organisation_id)
    organisation = (await session.exec(statement)).first()

    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    return organisation


OrgDep = Annotated[Organisation, Depends(get_current_org)]
