import logging

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)
auth_router = APIRouter(tags=["Authentication"])


ALB_AUTH_COOKIES = [
    "X-Amzn-Oidc-Data",
    "X-Amzn-Oidc-Data-0",
    "X-Amzn-Oidc-Data-1",
    "X-Amzn-Oidc-Data-2",
    "X-Amzn-Oidc-Data-3",
]

END_SESSION_ENDPOINT_STATIC = "https://sso.service.security.gov.uk/sign-out"


@auth_router.get("/signout")
async def sign_out(request: Request) -> RedirectResponse:
    """Sign out the user by clearing ALB authentication cookies and redirecting to the home page."""

    if request.app.state.idp_logout_url is None:
        logger.warning("Using static end session static endpoint as IdP logout URL was not resolved at startup")

    end_session_endpoint = request.app.state.idp_logout_url or END_SESSION_ENDPOINT_STATIC

    response = RedirectResponse(
        url=end_session_endpoint,
        status_code=302,
    )

    for cookie_name in ALB_AUTH_COOKIES:
        response.delete_cookie(cookie_name, path="/", secure=True, httponly=True)

    logger.info("User signed out, cleared ALB auth cookies")
    return response
