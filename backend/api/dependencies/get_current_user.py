import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col, select

from backend.api.dependencies.get_session import SQLSessionDep
from common.auth import get_user_info
from common.database.postgres_models import User, UserAuthEmail
from common.services.exceptions import MissingAuthTokenError
from common.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


async def record_user_auth_email(
    session: SQLSessionDep,
    user: User,
    email: str,
) -> None:
    statement = select(UserAuthEmail).where(UserAuthEmail.email == email)
    existing_auth_email = (await session.exec(statement)).first()

    if not existing_auth_email:
        statement = (
            insert(UserAuthEmail)
            .values(user_id=user.id, email=email)
            # Handle race condition when single user makes multiple requests
            .on_conflict_do_nothing(index_elements=["email"])
        )
        await session.exec(statement)


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
            # If IA has changed the subs, match on email then update to the new sub
            statement = (
                select(User)
                .join(UserAuthEmail, col(UserAuthEmail.user_id) == col(User.id))
                .where(
                    col(User.needs_to_update_sub).is_(True),  # flag set manually outside of code
                    UserAuthEmail.email == email,
                )
            )

            user = (await session.exec(statement)).first()
            if user:
                user.subject_id = subject_id

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

        await record_user_auth_email(session=session, user=user, email=email)
        user.needs_to_update_sub = False
        user.last_login = datetime.now(UTC)
        session.add(user)
        await session.commit()
        await session.refresh(user)

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
