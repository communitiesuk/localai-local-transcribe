import math

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from backend.utils.mappers import to_user_response
from common.database.postgres_models import Organisation, User
from common.types import PaginatedUsersResponse


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
    query = select(User).where(User.email == email)
    result = await session.exec(query)
    return result.one_or_none()


async def get_paginated_users(
    session,
    organisation: Organisation | None,
    page: int,
    page_size: int,
) -> PaginatedUsersResponse:
    count = await get_user_count(session, organisation=organisation)
    users = await get_users(
        session,
        organisation=organisation,
        page=page,
        page_size=page_size,
    )
    return PaginatedUsersResponse(
        items=[to_user_response(u) for u in users],
        total_count=count,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(count / page_size) or 1,
    )
