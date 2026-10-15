from __future__ import annotations

import asyncio

import pytest

from common.azure_apim_auth import AzureStaticTokenProvider
from evals.summarisation.src.common.adapter_factory import build_azure_apim_adapter
from evals.summarisation.src.common.apim_token_provider import ThreadSafeClientSecretTokenProvider


@pytest.mark.parametrize(
    ("url", "api_version", "key", "expected_error"),
    [
        ("", "2024-01-01", "key", "AZURE_APIM_URL is required"),
        ("https://example.com", "", "key", "AZURE_APIM_API_VERSION is required"),
        ("https://example.com", "2024-01-01", "", "AZURE_APIM_SUBSCRIPTION_KEY is required"),
    ],
)
def test_build_azure_apim_adapter_raises_when_missing_env_var(monkeypatch, url, api_version, key, expected_error):
    monkeypatch.setenv("AZURE_APIM_URL", url)
    monkeypatch.setenv("AZURE_APIM_API_VERSION", api_version)
    monkeypatch.setenv("AZURE_APIM_AUTH_METHOD", "static_token")
    monkeypatch.setenv("AZURE_APIM_ACCESS_TOKEN", "token")
    monkeypatch.setenv("AZURE_APIM_SUBSCRIPTION_KEY", key)

    with pytest.raises(ValueError, match=expected_error):
        build_azure_apim_adapter()


def test_build_azure_apim_adapter_success(monkeypatch):
    base_url = "https://api.example.com/openai/"
    api_version = "2024-02-15-preview"
    model_name = "gpt-4-turbo"

    monkeypatch.setenv("AZURE_APIM_URL", base_url)
    monkeypatch.setenv("AZURE_APIM_API_VERSION", api_version)
    monkeypatch.setenv("AZURE_APIM_AUTH_METHOD", "static_token")
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
    assert isinstance(adapter._token_provider, AzureStaticTokenProvider)  # noqa: SLF001
    assert client is not None
    assert str(client.base_url).rstrip("/") == f"{base_url.rstrip('/')}/{model_name}"
    assert "Ocp-Apim-Subscription-Key" in client.default_headers


def test_build_azure_apim_adapter_uses_client_secret_when_configured(monkeypatch):
    monkeypatch.setenv("AZURE_APIM_URL", "https://api.example.com/openai/")
    monkeypatch.setenv("AZURE_APIM_API_VERSION", "2024-02-15-preview")
    monkeypatch.setenv("AZURE_APIM_SUBSCRIPTION_KEY", "test-subscription-key-456")
    monkeypatch.setenv("AZURE_APIM_AUTH_METHOD", "client_secret")
    monkeypatch.setenv("AZURE_APIM_TENANT_ID", "test-tenant")
    monkeypatch.setenv("AZURE_APIM_CLIENT_ID", "test-client")
    monkeypatch.setenv("AZURE_APIM_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("AZURE_APIM_SCOPE", "api://example/.default")

    adapter = build_azure_apim_adapter()

    assert isinstance(adapter._token_provider, ThreadSafeClientSecretTokenProvider)  # noqa: SLF001
