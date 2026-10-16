import asyncio
import threading
from unittest.mock import MagicMock

import pytest

from common.azure_apim_auth import AzureClientSecretCredentialTokenProvider


@pytest.fixture
def provider():
    token_provider = AzureClientSecretCredentialTokenProvider(
        tenant_id="tenant", client_id="client", client_secret="secret", scope="https://example.com/.default"
    )

    # Mock the Azure Credential provider used within AzureClientSecretCredentialTokenProvider
    token_provider._azure_credential = MagicMock()  # noqa: SLF001
    token_provider._azure_credential.get_token = MagicMock(return_value=MagicMock(token="fake-token"))  # noqa: SLF001
    return token_provider


@pytest.mark.asyncio
async def test_get_token_fetches_token_on_first_call(provider):
    token = await provider.get_token()

    assert token == "fake-token"  # noqa: S105
    provider._azure_credential.get_token.assert_called_once_with("https://example.com/.default")  # noqa: SLF001


@pytest.mark.asyncio
async def test_get_token_returns_cached_token_without_re_fetching(provider):
    await provider.get_token()
    await provider.get_token()

    provider._azure_credential.get_token.assert_called_once()  # noqa: SLF001


@pytest.mark.asyncio
async def test_invalidate_token_causes_refetch(provider):
    provider._azure_credential.get_token = MagicMock(  # noqa: SLF001
        side_effect=[MagicMock(token="token-1"), MagicMock(token="token-2")]
    )

    await provider.get_token()
    await provider.invalidate_token()
    token = await provider.get_token()

    assert token == "token-2"  # noqa: S105
    assert provider._azure_credential.get_token.call_count == 2  # noqa: SLF001


@pytest.mark.asyncio
async def test_concurrent_get_token_calls_only_fetch_once(provider):
    tokens = await asyncio.gather(provider.get_token(), provider.get_token())

    assert all(t == "fake-token" for t in tokens)
    provider._azure_credential.get_token.assert_called_once()  # noqa: SLF001


def test_get_token_completes_when_called_from_separate_event_loops(provider):
    """Two threads, each with its own event loop, ask for a token at the same moment."""
    tokens: list[str] = []

    def request_token() -> None:
        tokens.append(asyncio.run(provider.get_token()))

    threads = [threading.Thread(target=request_token, daemon=True) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert tokens == ["fake-token", "fake-token"]
