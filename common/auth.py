import logging
from dataclasses import dataclass

import jwt
import requests

from common.services.exceptions import MissingAuthTokenError
from common.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_public_key_cache: dict[str, str] = {}


@dataclass
class UserAuthorisationResult:
    email: str
    is_authorised: bool
    auth_reason: str = ""


def _get_public_key(kid: str) -> str:
    if kid not in _public_key_cache:
        url = f"https://public-keys.auth.elb.{settings.AWS_REGION}.amazonaws.com/{kid}"
        _public_key_cache[kid] = requests.get(url, timeout=5).text
    return _public_key_cache[kid]


def _verify_and_decode_alb_jwt(token: str) -> dict:
    """Verify the ALB JWT signature, signer, and issuer, then return the decoded payload."""
    header = jwt.get_unverified_header(token)

    signer = header.get("signer")
    if signer != settings.ALB_ARN:
        msg = "JWT signer does not match expected ALB ARN"
        raise ValueError(msg)

    kid = header["kid"]
    public_key = _get_public_key(kid)

    try:
        return jwt.decode(
            token, public_key, algorithms=["ES256"], issuer=settings.OIDC_ISSUER, audience=settings.OIDC_CLIENT_ID
        )
    except jwt.DecodeError:
        # Evict cached key and retry once in case of key rotation
        _public_key_cache.pop(kid, None)
        public_key = _get_public_key(kid)
        return jwt.decode(
            token, public_key, algorithms=["ES256"], issuer=settings.OIDC_ISSUER, audience=settings.OIDC_CLIENT_ID
        )


def __load_dummy_user_info() -> UserAuthorisationResult:
    return UserAuthorisationResult(
        email="test@test.co.uk",
        is_authorised=True,
        auth_reason="LOCAL_TESTING",
    )


def get_user_info(auth_token: str | None) -> UserAuthorisationResult:
    """
    Retrieve user metadata from the x-amzn-oidc-data JWT injected by the ALB.
    Verifies the JWT signature, signer, and issuer before extracting claims.
    """
    if settings.ENVIRONMENT == "local":
        return __load_dummy_user_info()

    if not auth_token:
        raise MissingAuthTokenError

    try:
        payload = _verify_and_decode_alb_jwt(auth_token)
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
