from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from backend.api.routes.auth import ALB_AUTH_COOKIE_NAME, ALB_AUTH_COOKIE_SUFFIXES, END_SESSION_ENDPOINT_STATIC
from tests.utils import get_test_client


@pytest_asyncio.fixture
async def client():
    async with get_test_client() as ac:
        yield ac


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
    assert response.headers["location"] == END_SESSION_ENDPOINT_STATIC


@pytest.mark.asyncio
async def test_sign_out_clears_expected_alb_auth_cookies(client):
    with patch(
        "backend.api.routes.auth.get_idp_logout_url",
        AsyncMock(return_value=END_SESSION_ENDPOINT_STATIC),
    ):
        response = await client.get(
            "/signout",
            follow_redirects=False,
        )

    cookie_headers = response.headers.get_list("set-cookie")

    for suffix in ALB_AUTH_COOKIE_SUFFIXES:
        cookie_name = f"{ALB_AUTH_COOKIE_NAME}{suffix}"

        assert any(header.startswith(f"{cookie_name}=") for header in cookie_headers)

    assert not any(header.startswith("sessionid=") for header in cookie_headers)
