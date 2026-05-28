import pytest, pytest_asyncio
from unittest.mock import AsyncMock, patch

from backend.api.routes.auth import (
    ALB_AUTH_COOKIE_NAME,
    ALB_AUTH_COOKIE_PATTERN,
    auth_router,
    END_SESSION_ENDPOINT_STATIC
)
from tests.utils import get_test_client


@pytest_asyncio.fixture
async def client():
    async with get_test_client() as ac:
        yield ac



@pytest.mark.parametrize(
    ("cookie_name", "expected"),
    [
        # Base cookie
        (ALB_AUTH_COOKIE_NAME, True),

        # Valid suffixes
        (f"{ALB_AUTH_COOKIE_NAME}-0", True),
        (f"{ALB_AUTH_COOKIE_NAME}-1", True),
        (f"{ALB_AUTH_COOKIE_NAME}-999", True),

        # Wrong cookie 
        ("sessionid", False),

        # Incorrect suffix 
        (f"{ALB_AUTH_COOKIE_NAME}-test", False),

        # No suffix 
        (f"{ALB_AUTH_COOKIE_NAME}-", False),

        # Extra trailing chars
        (f"{ALB_AUTH_COOKIE_NAME}-1-extra", False),

        # Prefix 
        (f"my-{ALB_AUTH_COOKIE_NAME}", False),

        # Empty
        ("", False),

        # Case sensitivity
        (ALB_AUTH_COOKIE_NAME.lower(), False),
    ],
)
def test_alb_auth_cookie_pattern(cookie_name: str, expected: bool):
    assert (
        ALB_AUTH_COOKIE_PATTERN.fullmatch(cookie_name) is not None
    ) is expected



@pytest.mark.asyncio
async def test_sign_out_redirects_to_idp(client):
    with patch(
        "backend.utils.get_idp_logout_url.get_idp_logout_url",
        AsyncMock(return_value=END_SESSION_ENDPOINT_STATIC),
    ):
        response = await client.get(
            "/signout",
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert (
        response.headers["location"]
        == END_SESSION_ENDPOINT_STATIC
    )


@pytest.mark.asyncio
async def test_sign_out_clears_alb_auth_cookies_only(client):
    client.cookies.clear()
    client.cookies.set(
        ALB_AUTH_COOKIE_NAME,
        "token",
    )
    client.cookies.set(
        f"{ALB_AUTH_COOKIE_NAME}-0",
        "token-shard",
    )
    client.cookies.set(
        "sessionid",
        "keep",
    )
    with patch(
        "backend.utils.get_idp_logout_url.get_idp_logout_url",
        AsyncMock(return_value=END_SESSION_ENDPOINT_STATIC),
    ):
        response = await client.get(
            "/signout",
            follow_redirects=False,
        )

    set_cookie_headers = response.headers.get_list(
        "set-cookie"
    )

    assert any(
        f"{ALB_AUTH_COOKIE_NAME}="
        in header
        for header in set_cookie_headers
    )

    assert any(
        f"{ALB_AUTH_COOKIE_NAME}-0="
        in header
        for header in set_cookie_headers
    )

    assert not any(
        "sessionid="
        in header
        for header in set_cookie_headers
    )