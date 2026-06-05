import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse

from backend.utils.get_idp_logout_url import get_idp_logout_url
from common.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
auth_router = APIRouter(tags=["Authentication"])


ALB_AUTH_COOKIE_NAME = "X-Amzn-Oidc-Data"
ALB_AUTH_COOKIE_SUFFIXES = ["", "-0", "-1", "-2", "-3"]  # ALB can potentially set multiple cookies with these suffixes

END_SESSION_ENDPOINT_STATIC = "https://sso.service.security.gov.uk/sign-out"


@auth_router.get("/signout")
async def sign_out(request: Request) -> RedirectResponse:
    """Sign out the user by clearing ALB auth cookies and redirecting to the IdP."""

    end_session_endpoint = await get_idp_logout_url() or END_SESSION_ENDPOINT_STATIC
    domain = request.url.hostname

    response = RedirectResponse(
        url=end_session_endpoint,
        status_code=status.HTTP_302_FOUND,
    )

    for suffix in ALB_AUTH_COOKIE_SUFFIXES:
        cookie_name = f"{ALB_AUTH_COOKIE_NAME}{suffix}"
        response.delete_cookie(
            cookie_name,
            path="/",
            domain=domain,
            secure=True,
            httponly=True,
        )

    logger.info("User redirected to IdP logout endpoint: %s from %s", end_session_endpoint, domain)

    return response
