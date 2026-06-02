from sqlmodel import select, func, col
from sqlmodel.ext.asyncio.session import AsyncSession

from common.database.postgres_models import Organisation, User


async def get_users(
        session: AsyncSession, 
        organisation: Organisation | None = None,
        page: int = 1,
        page_size: int = 10,
) -> list[User]:
    offset = (page - 1) * page_size

    statement = select(User)

    if organisation:
        statement = statement.where(
            User.organisation_id == organisation.id
        )

    statement = (
        statement
        .offset(offset)
        .limit(page_size)
    )

    result = await session.exec(statement)
    return list(result.all())


async def get_user_count(
    session: AsyncSession,
    organisation: Organisation | None = None,
):
    statement = select(func.count(col(User.id)))

    if organisation:
        statement = statement.where(
            User.organisation_id == organisation.id
        )

    result = await session.exec(statement)
    return result.one()