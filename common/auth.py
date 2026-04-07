import logging
from dataclasses import dataclass

import jwt

from common.services.exceptions import MissingAuthTokenError
from common.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class UserAuthorisationResult:
    email: str
    is_authorised: bool
    auth_reason: str = ""


def __load_dummy_user_info() -> UserAuthorisationResult:
    return UserAuthorisationResult(
        email="test@test.co.uk",
        is_authorised=True,
        auth_reason="LOCAL_TESTING",
    )


def get_user_info(auth_token: str | None) -> UserAuthorisationResult:
    """
    Retrieve user metadata from the x-amzn-oidc-data JWT injected by the ALB.
    """
    if settings.ENVIRONMENT == "local":
        return __load_dummy_user_info()

    if not auth_token:
        raise MissingAuthTokenError

    try:
        payload = jwt.decode(auth_token, options={"verify_signature": False}, algorithms=["ES256"])
        email = payload.get("email")
        if not email:
            msg = "No email found in JWT payload"
            raise ValueError(msg)
        return UserAuthorisationResult(email=email, is_authorised=True)
    except Exception:
        logger.exception("Error occurred when authorising user")
        raise


def is_authorised_user(auth_token: str) -> bool:
    """
    A simple wrapper function to check the user is permitted to access the resource.
    """
    try:
        return get_user_info(auth_token).is_authorised
    except Exception:
        logger.exception("Error occurred when authorising user")
        return False
