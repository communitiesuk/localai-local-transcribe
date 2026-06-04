from typing import Annotated

from fastapi import Depends, HTTPException

from backend.api.dependencies.get_current_user import UserDep
from common.auth import is_system_admin
from common.database.postgres_models import User


async def get_system_admin(
    user: UserDep,
) -> User:
    if not is_system_admin(user):
        raise HTTPException(
            status_code=403,
            detail="Only a system admin can perform this action",
        )

    return user


SystemAdminDep = Annotated[User, Depends(get_system_admin)]
