from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from common.database.postgres_models import Organisation, User


async def get_users(session: AsyncSession, organisation: Organisation | None = None) -> list[User]:
    statement = select(User).where(User.organisation_id == organisation.id) if organisation else select(User)
    return list((await session.exec(statement)).all())
