from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from common.services.transcription_services.azure_stt_base import HTTP_UNAUTHORIZED, make_stt_request

_MODULE = "common.services.transcription_services.azure_stt_base"


def _mock_response(status_code: int) -> httpx.Response:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    return response


@pytest.fixture
def mock_token_provider():
    provider = AsyncMock()
    provider.get_token = AsyncMock(return_value="token-1")
    provider.invalidate_token = AsyncMock()
    return provider


@pytest.fixture(autouse=True)
def patch_apim_token_provider(mock_token_provider):
    with patch(f"{_MODULE}.get_stt_token_provider", return_value=mock_token_provider):
        yield mock_token_provider


@pytest.mark.asyncio
async def test_successful_request_passes_bearer_token(mock_token_provider):
    mock_token_provider.get_token = AsyncMock(return_value="my-token")
    received_headers: dict[str, str] = {}

    async def make_request(headers: dict[str, str]) -> httpx.Response:
        received_headers.update(headers)
        return _mock_response(200)

    with patch(f"{_MODULE}.settings") as mock_settings:
        mock_settings.AZURE_APIM_SUBSCRIPTION_KEY = "sub-key"
        await make_stt_request(make_request)

    assert received_headers["Authorization"] == "Bearer my-token"
    assert received_headers["Ocp-Apim-Subscription-Key"] == "sub-key"
    mock_token_provider.invalidate_token.assert_not_called()


@pytest.mark.asyncio
async def test_401_triggers_token_invalidation_and_retry(mock_token_provider):
    mock_token_provider.get_token = AsyncMock(side_effect=["stale-token", "fresh-token"])
    call_count = 0

    async def make_request(_headers: dict[str, str]) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return _mock_response(HTTP_UNAUTHORIZED if call_count == 1 else 200)

    with patch(f"{_MODULE}.settings"):
        response = await make_stt_request(make_request)

    assert response.status_code == 200
    assert call_count == 2
    mock_token_provider.invalidate_token.assert_called_once()


@pytest.mark.asyncio
async def test_double_401_returns_second_401_without_extra_invalidation(mock_token_provider):
    async def make_request(_headers: dict[str, str]) -> httpx.Response:
        return _mock_response(HTTP_UNAUTHORIZED)

    with patch(f"{_MODULE}.settings"):
        response = await make_stt_request(make_request)

    assert response.status_code == HTTP_UNAUTHORIZED
    mock_token_provider.invalidate_token.assert_called_once()


@pytest.mark.asyncio
async def test_non_401_error_returns_immediately_without_retry(mock_token_provider):
    call_count = 0

    async def make_request(_headers: dict[str, str]) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return _mock_response(500)

    with patch(f"{_MODULE}.settings"):
        response = await make_stt_request(make_request)

    assert response.status_code == 500
    assert call_count == 1
    mock_token_provider.invalidate_token.assert_not_called()


@pytest.mark.asyncio
async def test_extra_headers_are_forwarded_to_request():
    received_headers: dict[str, str] = {}

    async def make_request(headers: dict[str, str]) -> httpx.Response:
        received_headers.update(headers)
        return _mock_response(200)

    with patch(f"{_MODULE}.settings"):
        await make_stt_request(make_request, extra_headers={"Content-Type": "application/json"})

    assert received_headers["Content-Type"] == "application/json"
