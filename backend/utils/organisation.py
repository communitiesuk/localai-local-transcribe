from uuid import UUID

from sqlmodel import select

from backend.api.dependencies import SQLSessionDep
from common.database.postgres_models import Organisation


async def organisation_from_id(session: SQLSessionDep, organisation_id: UUID) -> Organisation | None:
    statement = select(Organisation).where(Organisation.id == organisation_id)

    return (await session.exec(statement)).first()
