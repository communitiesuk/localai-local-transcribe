from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from backend.api.dependencies.get_session import SQLSessionDep
from backend.utils.queries import user_from_id
from common.database.postgres_models import User


async def get_target_user(
    user_id: UUID,
    session: SQLSessionDep,
) -> User:
    user = await user_from_id(session, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


TargetUserDep = Annotated[User, Depends(get_target_user)]
