from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlmodel import select

from backend.api.dependencies.get_session import SQLSessionDep
from common.database.postgres_models import Organisation


async def get_organisation(
    organisation_id: UUID,
    session: SQLSessionDep,
) -> Organisation:
    statement = select(Organisation).where(Organisation.id == organisation_id)
    organisation = (await session.exec(statement)).first()

    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    return organisation


OrganisationDep = Annotated[Organisation, Depends(get_organisation)]
