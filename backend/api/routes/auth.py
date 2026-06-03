import logging
import re

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from backend.utils.get_idp_logout_url import get_idp_logout_url
from common.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
auth_router = APIRouter(tags=["Authentication"])


ALB_AUTH_COOKIE_NAME = settings.ALB_COOKIE_NAME
ALB_AUTH_COOKIE_PATTERN = re.compile(rf"^{re.escape(ALB_AUTH_COOKIE_NAME)}(?:-\d+)?$")

END_SESSION_ENDPOINT_STATIC = "https://sso.service.security.gov.uk/sign-out"


@auth_router.get("/signout")
async def sign_out(request: Request) -> RedirectResponse:
    """Sign out the user by clearing ALB auth cookies and redirecting to the IdP."""

    end_session_endpoint = await get_idp_logout_url() or END_SESSION_ENDPOINT_STATIC
    
    logger.info("Signing out user, redirecting to IdP logout endpoint: {endpoint}", endpoint=end_session_endpoint)
    logger.info("Incoming cookies: %s", request.cookies)
    logger.info("ALB cookie name for matching: %s", ALB_AUTH_COOKIE_NAME)

    response = RedirectResponse(
        url=end_session_endpoint,
        status_code=302,
    )

    for cookie_name in request.cookies:
        if ALB_AUTH_COOKIE_PATTERN.fullmatch(cookie_name):
            logger.info("Clearing cookie: %s", cookie_name)
            response.delete_cookie(
                cookie_name,
                path="/",
                secure=True,
                httponly=True,
            )

    logger.info("User signed out, cleared ALB auth cookies")
    logger.info("Response headers after clearing cookies: %s", response.headers)

    return response
