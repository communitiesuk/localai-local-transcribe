from __future__ import annotations

import asyncio
import threading
from functools import cache
from typing import Protocol

from azure.identity import ClientSecretCredential

from common.settings import get_settings


class AzureTokenProvider(Protocol):
    async def get_token(self) -> str: ...
    async def invalidate_token(self) -> None: ...


class AzureStaticTokenProvider:
    """Basic token provider which always returns the token it was initialised with."""

    def __init__(self, token: str) -> None:
        self._token = token

    async def get_token(self) -> str:
        return self._token

    async def invalidate_token(self) -> None:
        pass


class AzureClientSecretCredentialTokenProvider:
    """Gets AI Gateway tokens with a client secret, and is safe to call from many threads.

    The evaluation framework runs each model call in its own thread with its own event loop.
    An asyncio lock and an asynchronous credential belong to a single event loop. A call waiting
    on that lock from a second event loop is never woken, so it stalls until its timeout and
    leaves a thread that stops the process from exiting. This provider uses the synchronous
    credential and a threading lock instead. The credential keeps its own token cache and can be
    called from any thread.
    """

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, scope: str) -> None:
        self._refresh_lock = threading.Lock()
        self._token: str | None = None
        self._token_valid: bool = False
        self._azure_credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        self.scope = scope

    def _refresh_token(self) -> str:
        """Fetch a token if the local cache is empty or has been marked invalid."""
        with self._refresh_lock:
            if self._token_valid and self._token:
                return self._token
            result = self._azure_credential.get_token(self.scope)
            self._token = result.token
            self._token_valid = True
            return self._token

    async def get_token(self) -> str:
        if self._token_valid and self._token:
            return self._token
        # The synchronous call blocks, so it runs in a worker thread to keep the event loop free.
        return await asyncio.to_thread(self._refresh_token)

    async def invalidate_token(self) -> None:
        self._token_valid = False


@cache
def get_azure_client_secret_token_provider(
    tenant_id: str, client_id: str, client_secret: str, scope: str
) -> AzureTokenProvider:
    """Returns a cached AzureClientSecretTokenProvider for the given credentials."""
    return AzureClientSecretCredentialTokenProvider(tenant_id, client_id, client_secret, scope)


def build_azure_apim_token_provider() -> AzureTokenProvider:
    """Factory that builds the appropriate APIM token provider based on settings."""
    settings = get_settings()
    if settings.AZURE_APIM_AUTH_METHOD == "client_secret":
        if not settings.AZURE_APIM_TENANT_ID:
            msg = "AZURE_APIM_TENANT_ID is required for azure_apim client_secret auth"
            raise ValueError(msg)
        if not settings.AZURE_APIM_CLIENT_ID:
            msg = "AZURE_APIM_CLIENT_ID is required for azure_apim client_secret auth"
            raise ValueError(msg)
        if not settings.AZURE_APIM_CLIENT_SECRET:
            msg = "AZURE_APIM_CLIENT_SECRET is required for azure_apim client_secret auth"
            raise ValueError(msg)
        if not settings.AZURE_APIM_SCOPE:
            msg = "AZURE_APIM_SCOPE is required for azure_apim client_secret auth"
            raise ValueError(msg)
        return get_azure_client_secret_token_provider(
            settings.AZURE_APIM_TENANT_ID,
            settings.AZURE_APIM_CLIENT_ID,
            settings.AZURE_APIM_CLIENT_SECRET,
            settings.AZURE_APIM_SCOPE,
        )
    if settings.AZURE_APIM_AUTH_METHOD == "static_token":
        if not settings.AZURE_APIM_ACCESS_TOKEN:
            msg = "AZURE_APIM_ACCESS_TOKEN is required for azure_apim static_token auth"
            raise ValueError(msg)
        return AzureStaticTokenProvider(settings.AZURE_APIM_ACCESS_TOKEN)
    msg = "AZURE_APIM_AUTH_METHOD is required, use either 'static_token' or 'client_secret'"
    raise ValueError(msg)
