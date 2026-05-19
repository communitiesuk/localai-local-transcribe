from common.database.postgres_models import User
from common.types import GetUserResponse


def to_user_response(user: User) -> GetUserResponse:
    return GetUserResponse(
        id=user.id,
        created_datetime=user.created_datetime,
        updated_datetime=user.updated_datetime,
        email=user.email,
        data_retention_days=user.data_retention_days,
        roles=user.roles,
    )
