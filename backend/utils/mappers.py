from datetime import UTC, datetime, timedelta

from backend.utils.constants import INACTIVITY_PERIOD
from common.database.postgres_models import User
from common.types import GetUserResponse


def to_user_response(user: User) -> GetUserResponse:
    is_active = user.last_login >= datetime.now(UTC) - timedelta(days=INACTIVITY_PERIOD)

    return GetUserResponse(
        id=user.id,
        created_datetime=user.created_datetime,
        updated_datetime=user.updated_datetime,
        accepted_tou=user.accepted_tou,
        last_login=user.last_login,
        is_active=is_active,
        name=user.name,
        email=user.email,
        data_retention_days=user.data_retention_days,
        roles=user.roles,
        organisation_id=user.organisation_id,
    )
