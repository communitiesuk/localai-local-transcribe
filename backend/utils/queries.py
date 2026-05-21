from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from common.database.postgres_models import Organisation, User


async def organisation_from_id(session: AsyncSession, organisation_id: UUID) -> Organisation | None:
    return await session.get(Organisation, organisation_id)


async def user_from_id(
    session: AsyncSession,
    user_id: UUID,
) -> User | None:
    return await session.get(User, user_id)


async def get_users(session: AsyncSession, organisation: Organisation | None = None) -> list[User]:
    statement = select(User).where(User.organisation_id == organisation.id) if organisation else select(User)
    return list((await session.exec(statement)).all())
