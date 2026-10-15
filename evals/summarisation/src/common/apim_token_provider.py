from __future__ import annotations

import asyncio
from functools import cache

from azure.identity import ClientSecretCredential


class ThreadSafeClientSecretTokenProvider:
    """Gets AI Gateway tokens with a client secret, and is safe to call from many threads.

    The evaluation framework runs each model call in its own thread with its own event loop.
    The shared provider in common.azure_apim_auth holds one asyncio lock and one asynchronous
    credential, which belong to a single event loop. A call waiting on that lock from a second
    event loop is never woken, so it stalls until its timeout and leaves a thread that stops the
    process from exiting. This provider uses the synchronous credential instead. That credential
    keeps its own token cache and can be called from any thread, so no lock is needed.
    """

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, scope: str) -> None:
        self._credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        self._scope = scope

    async def get_token(self) -> str:
        """Returns a valid token, asking Microsoft Entra ID only when the cached one is near expiry."""
        # The synchronous call blocks, so it runs in a worker thread to keep the event loop free.
        access_token = await asyncio.to_thread(self._credential.get_token, self._scope)
        return access_token.token

    async def invalidate_token(self) -> None:
        """Does nothing, because the credential already refreshes tokens before they expire."""


@cache
def get_thread_safe_client_secret_token_provider(
    tenant_id: str, client_id: str, client_secret: str, scope: str
) -> ThreadSafeClientSecretTokenProvider:
    """Returns one shared provider per set of credentials, so every call reuses the same token cache."""
    return ThreadSafeClientSecretTokenProvider(tenant_id, client_id, client_secret, scope)
