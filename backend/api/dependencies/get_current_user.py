import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlmodel import col, select

from backend.api.dependencies.get_session import SQLSessionDep
from common.auth import get_user_info
from common.database.postgres_models import AnalyticsEventType, User
from common.services.analytics_service import record_analytics_event
from common.services.exceptions import MissingAuthTokenError
from common.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


async def get_current_user(
    session: SQLSessionDep,
    x_amzn_oidc_data: Annotated[str | None, Header()] = None,
) -> User:
    """
    Called on every endpoint to decode JWT passed in every request.
    Gets the user based on the email in the JWT
    Args:
        x_amzn_oidc_data: The incoming JWT from the auth provider, passed via the frontend app
    Returns:
        User: The user matching the username in the token
    """

    authorization: str | None = x_amzn_oidc_data

    try:
        user_auth_info = get_user_info(authorization)
        email = user_auth_info.email
        subject_id = user_auth_info.subject_id

        unauthorised_error = HTTPException(
            status_code=401,
            detail="User does not have the required permissions to access this resource",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not user_auth_info.is_authorised:
            logger.info("User %s does not have the required permissions", email)
            raise unauthorised_error

        statement = select(User).where(User.subject_id == subject_id)
        user = (await session.exec(statement)).first()

        if not user:
            # Try to find user by email address, this is a fallback for legacy
            # accounts which do not yet have a subject id associated.
            # After this login, a subject id will be added to the account and login
            # matching by email should no longer be possible
            statement = select(User).where(User.email == email, col(User.subject_id).is_(None))
            user = (await session.exec(statement)).first()

        if not user:
            # Do not automatically create new accounts on login
            raise unauthorised_error

        # Update subject_id if it has changed (e.g. legacy account matched by email)
        if user.subject_id != subject_id:
            user.subject_id = subject_id
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # A user is authenticated on every request (the ALB re-validates the JWT each time), so only record an
        # analytics event when enough time has passed since the last one to look like a new session, rather than
        # recording one per request.
        now = datetime.now(UTC)
        session_gap = timedelta(minutes=settings.ANALYTICS_AUTHENTICATION_SESSION_GAP_MINUTES)
        is_new_session = (now - user.last_login) > session_gap

        user.last_login = now
        await session.commit()

        if is_new_session:
            await record_analytics_event(
                session, AnalyticsEventType.USER_AUTHENTICATED, user.evaluation_id, user.organisation_id
            )

        return user
    except MissingAuthTokenError as e:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except HTTPException:
        logger.exception("Unhandled HTTP exception")
        raise
    except Exception as e:
        logger.exception("Unhandled exception when getting user")
        raise HTTPException(
            status_code=500,
            detail="Unhandled Authorisation Error",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


PendingTouUserDep = Annotated[User, Depends(get_current_user)]


async def require_accepted_tou(user: PendingTouUserDep) -> User:
    if not user.accepted_tou:
        raise HTTPException(
            status_code=403,
            detail="Terms of use must be accepted",
        )

    return user


UserDep = Annotated[User, Depends(require_accepted_tou)]
