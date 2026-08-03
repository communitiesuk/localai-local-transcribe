from __future__ import annotations

import asyncio

import pytest

from evals.summarisation.src.common.adapter_factory import build_azure_apim_adapter


@pytest.mark.parametrize(
    ("url", "api_version", "token", "key", "expected_error"),
    [
        ("", "2024-01-01", "token", "key", "AZURE_APIM_URL is required"),
        ("https://example.com", "", "token", "key", "AZURE_APIM_API_VERSION is required"),
        ("https://example.com", "2024-01-01", "", "key", "AZURE_APIM_ACCESS_TOKEN is required"),
        ("https://example.com", "2024-01-01", "token", "", "AZURE_APIM_SUBSCRIPTION_KEY is required"),
    ],
)
def test_build_azure_apim_adapter_raises_when_missing_env_var(
    monkeypatch, url, api_version, token, key, expected_error
):
    monkeypatch.setenv("AZURE_APIM_URL", url)
    monkeypatch.setenv("AZURE_APIM_API_VERSION", api_version)
    monkeypatch.setenv("AZURE_APIM_ACCESS_TOKEN", token)
    monkeypatch.setenv("AZURE_APIM_SUBSCRIPTION_KEY", key)

    with pytest.raises(ValueError, match=expected_error):
        build_azure_apim_adapter()


def test_build_azure_apim_adapter_success(monkeypatch):
    base_url = "https://api.example.com/openai/"
    api_version = "2024-02-15-preview"
    model_name = "gpt-4-turbo"

    monkeypatch.setenv("AZURE_APIM_URL", base_url)
    monkeypatch.setenv("AZURE_APIM_API_VERSION", api_version)
    monkeypatch.setenv("AZURE_APIM_ACCESS_TOKEN", "test-access-token-123")
    monkeypatch.setenv("AZURE_APIM_SUBSCRIPTION_KEY", "test-subscription-key-456")
    monkeypatch.setenv("BEST_LLM_MODEL_NAME", model_name)

    adapter = build_azure_apim_adapter()
    client = asyncio.run(adapter._get_apim_client())  # noqa: SLF001

    assert isinstance(adapter, type(adapter))
    assert adapter._model == model_name  # noqa: SLF001
    assert adapter._api_version == api_version  # noqa: SLF001
    assert adapter._url == base_url  # noqa: SLF001
    assert adapter._subscription_key == "test-subscription-key-456"  # noqa: SLF001
    assert client is not None
    assert str(client.base_url).rstrip("/") == f"{base_url.rstrip('/')}/{model_name}"
    assert "Ocp-Apim-Subscription-Key" in client.default_headers


# --- the adapter is reused across calls, but never across a token change ---


@pytest.fixture
def apim_env(monkeypatch):
    """Configure APIM settings, returning a setter for the access token."""
    monkeypatch.setenv("AZURE_APIM_URL", "https://api.example.com/openai/")
    monkeypatch.setenv("AZURE_APIM_API_VERSION", "2024-02-15-preview")
    monkeypatch.setenv("AZURE_APIM_SUBSCRIPTION_KEY", "test-subscription-key")

    def _set_token(token: str) -> None:
        monkeypatch.setenv("AZURE_APIM_ACCESS_TOKEN", token)

    _set_token("token-one")
    return _set_token


def test_adapter_is_reused_across_calls(apim_env):  # noqa: ARG001
    """A fresh adapter per judge call throws away its HTTP client, so every call redoes TLS setup."""
    assert build_azure_apim_adapter() is build_azure_apim_adapter()


def test_adapter_is_rebuilt_when_the_access_token_changes(apim_env):
    """``apim.sh`` rewrites the token mid-run; a pinned adapter would keep using the expired one."""
    first = build_azure_apim_adapter()

    apim_env("token-two")
    second = build_azure_apim_adapter()

    assert second is not first
    assert asyncio.run(second._get_apim_client()).api_key == "token-two"  # noqa: SLF001
