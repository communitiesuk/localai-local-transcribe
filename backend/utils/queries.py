from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from common.database.postgres_models import Organisation, User


async def get_users(
    session: AsyncSession,
    organisation: Organisation | None = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> list[User]:
    offset = (page - 1) * page_size

    statement = select(User)

    if organisation:
        statement = statement.where(User.organisation_id == organisation.id)

    statement = statement.offset(offset).limit(page_size)

    result = await session.exec(statement)
    return list(result.all())


async def get_user_count(
    session: AsyncSession,
    organisation: Organisation | None = None,
) -> int:
    statement = select(func.count(col(User.id)))

    if organisation:
        statement = statement.where(User.organisation_id == organisation.id)

    result = await session.exec(statement)
    return result.one()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    normalized_email = email.lower()
    query = select(User).where(func.lower(User.email) == normalized_email)
    result = await session.execute(query)
    return result.scalar_one_or_none()
