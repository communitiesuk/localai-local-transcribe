from collections.abc import Awaitable, Callable
from functools import cache
from typing import Any

import httpx

from common.azure_apim_auth import AzureTokenProvider, build_azure_apim_token_provider
from common.database.postgres_models import DialogueEntry
from common.settings import get_settings

TOO_MANY_REQUESTS = 429
HTTP_UNAUTHORIZED = 401

settings = get_settings()


@cache
def get_stt_token_provider() -> AzureTokenProvider:
    return build_azure_apim_token_provider()


async def make_stt_request(
    make_request: Callable[[dict[str, str]], Awaitable[httpx.Response]],
    extra_headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Makes an HTTP request, refreshing the APIM token once on 401."""
    provider = get_stt_token_provider()

    async def _do_request() -> httpx.Response:
        token = await provider.get_token()
        headers = {
            "Ocp-Apim-Subscription-Key": settings.AZURE_APIM_SUBSCRIPTION_KEY or "",
            "Authorization": f"Bearer {token}",
            **(extra_headers or {}),
        }
        return await make_request(headers)

    response = await _do_request()
    if response.status_code == HTTP_UNAUTHORIZED:
        await provider.invalidate_token()
        response = await _do_request()
    return response


def stt_is_available() -> bool:
    """Returns True if APIM STT credentials are properly configured."""
    if not settings.AZURE_APIM_URL or not settings.AZURE_APIM_SUBSCRIPTION_KEY:
        return False
    if settings.AZURE_APIM_AUTH_METHOD == "client_secret":
        return bool(
            settings.AZURE_APIM_TENANT_ID
            and settings.AZURE_APIM_CLIENT_ID
            and settings.AZURE_APIM_CLIENT_SECRET
            and settings.AZURE_APIM_SCOPE
        )
    if settings.AZURE_APIM_AUTH_METHOD == "static_token":
        return bool(settings.AZURE_APIM_ACCESS_TOKEN)
    return False


def convert_to_dialogue_entries(phrases: list[dict[str, Any]]) -> list[DialogueEntry]:
    return [
        DialogueEntry(
            speaker=str(entry["speaker"]),
            text=entry["text"],
            start_time=float(entry["offsetMilliseconds"]) / 1000,
            end_time=(float(entry["offsetMilliseconds"]) + float(entry["durationMilliseconds"])) / 1000,
        )
        for entry in phrases
    ]
