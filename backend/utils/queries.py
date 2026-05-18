from uuid import UUID

from sqlmodel import select

from backend.api.dependencies import SQLSessionDep
from common.database.postgres_models import Organisation, User


async def organisation_from_id(session: SQLSessionDep, organisation_id: UUID) -> Organisation | None:
    statement = select(Organisation).where(Organisation.id == organisation_id)
    return (await session.exec(statement)).first()


async def user_from_id(
    session: SQLSessionDep,
    user_id: UUID,
) -> User | None:
    statement = select(User).where(User.id == user_id)
    return (await session.exec(statement)).first()


async def get_users(session: SQLSessionDep, organisation: Organisation | None = None):
    statement = select(User).where(User.organisation_id == organisation.id) if organisation else select(User)
    return list((await session.exec(statement)).all())
