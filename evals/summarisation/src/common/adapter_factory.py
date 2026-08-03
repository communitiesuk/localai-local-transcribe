from __future__ import annotations

from functools import lru_cache

from common.azure_apim_auth import AzureStaticTokenProvider
from common.llm.adapters import AzureAPIMModelAdapter
from common.settings import get_settings


@lru_cache(maxsize=1)
def _adapter(url: str, model: str, api_version: str, token: str, subscription_key: str) -> AzureAPIMModelAdapter:
    """Memoised so judge calls share one adapter, and with it one pooled HTTP client.

    Keyed on the token rather than cached outright: ``AzureStaticTokenProvider`` closes over the token
    it is given, so an adapter pinned across a token refresh would keep presenting the expired one.
    """
    return AzureAPIMModelAdapter(
        url=url,
        model=model,
        api_version=api_version,
        token_provider=AzureStaticTokenProvider(token),
        subscription_key=subscription_key,
    )


def build_azure_apim_adapter() -> AzureAPIMModelAdapter:
    """Builds Azure APIM model adapter from environment settings."""
    settings = get_settings()
    if not settings.AZURE_APIM_URL:
        msg = "AZURE_APIM_URL is required"
        raise ValueError(msg)
    if not settings.AZURE_APIM_API_VERSION:
        msg = "AZURE_APIM_API_VERSION is required"
        raise ValueError(msg)
    if not settings.AZURE_APIM_ACCESS_TOKEN:
        msg = "AZURE_APIM_ACCESS_TOKEN is required"
        raise ValueError(msg)
    if not settings.AZURE_APIM_SUBSCRIPTION_KEY:
        msg = "AZURE_APIM_SUBSCRIPTION_KEY is required"
        raise ValueError(msg)

    return _adapter(
        settings.AZURE_APIM_URL,
        settings.BEST_LLM_MODEL_NAME,
        settings.AZURE_APIM_API_VERSION,
        settings.AZURE_APIM_ACCESS_TOKEN,
        settings.AZURE_APIM_SUBSCRIPTION_KEY,
    )
