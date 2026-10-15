from __future__ import annotations

from common.azure_apim_auth import build_azure_apim_token_provider
from common.llm.adapters import AzureAPIMModelAdapter
from common.settings import get_settings


def build_azure_apim_adapter() -> AzureAPIMModelAdapter:
    """Builds Azure APIM model adapter from environment settings.

    The token provider follows AZURE_APIM_AUTH_METHOD, so the pipelines can obtain their own
    token with a client secret instead of using a copied-in bearer token.
    """
    settings = get_settings()
    if not settings.AZURE_APIM_URL:
        msg = "AZURE_APIM_URL is required"
        raise ValueError(msg)
    if not settings.AZURE_APIM_API_VERSION:
        msg = "AZURE_APIM_API_VERSION is required"
        raise ValueError(msg)
    if not settings.AZURE_APIM_SUBSCRIPTION_KEY:
        msg = "AZURE_APIM_SUBSCRIPTION_KEY is required"
        raise ValueError(msg)

    return AzureAPIMModelAdapter(
        url=settings.AZURE_APIM_URL,
        model=settings.BEST_LLM_MODEL_NAME,
        api_version=settings.AZURE_APIM_API_VERSION,
        token_provider=build_azure_apim_token_provider(),
        subscription_key=settings.AZURE_APIM_SUBSCRIPTION_KEY,
    )
