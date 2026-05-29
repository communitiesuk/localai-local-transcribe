from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from backend.api.dependencies.get_session import SQLSessionDep
from common.database.postgres_models import User


async def get_target_user(
    user_id: UUID,
    session: SQLSessionDep,
) -> User:
    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


TargetUserDep = Annotated[User, Depends(get_target_user)]
