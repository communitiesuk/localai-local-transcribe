from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace

from evals.summarisation.src.common import apim_token_provider
from evals.summarisation.src.common.apim_token_provider import ThreadSafeClientSecretTokenProvider


class _FakeCredential:
    """Stands in for the Azure credential and records the scope it was asked for."""

    def __init__(self, *_credentials: str) -> None:
        self.scopes: list[str] = []

    def get_token(self, scope: str) -> SimpleNamespace:
        self.scopes.append(scope)
        return SimpleNamespace(token="fake-token")


def test_get_token_returns_token_for_scope(monkeypatch):
    monkeypatch.setattr(apim_token_provider, "ClientSecretCredential", _FakeCredential)
    provider = ThreadSafeClientSecretTokenProvider("tenant", "client", "secret", "api://example/.default")

    token = asyncio.run(provider.get_token())

    assert token == "fake-token"  # noqa: S105
    assert provider._credential.scopes == ["api://example/.default"]  # noqa: SLF001


def test_get_token_completes_when_called_from_separate_event_loops(monkeypatch):
    """Two threads, each with its own event loop, ask for a token at the same moment."""
    monkeypatch.setattr(apim_token_provider, "ClientSecretCredential", _FakeCredential)
    provider = ThreadSafeClientSecretTokenProvider("tenant", "client", "secret", "api://example/.default")
    tokens: list[str] = []

    def request_token() -> None:
        tokens.append(asyncio.run(provider.get_token()))

    threads = [threading.Thread(target=request_token, daemon=True) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert tokens == ["fake-token", "fake-token"]
