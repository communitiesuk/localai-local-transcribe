from __future__ import annotations

import os

from common.apim_auth import AzureStaticTokenProvider
from common.llm.adapters import AzureAPIMModelAdapter, BedrockAPIMModelAdapter
from common.settings import get_settings


def resolve_judge_model_name(best_model_name: str | None = None) -> str:
    """Resolve the judge model, falling back to the configured best model."""
    if best_model_name is None:
        best_model_name = get_settings().BEST_LLM_MODEL_NAME
    return os.environ.get("JUDGE_LLM_MODEL_NAME") or best_model_name


def build_azure_apim_adapter() -> AzureAPIMModelAdapter:
    """Builds Azure APIM model adapter from environment settings.

    Used only by the LLM judge (evals.summarisation.src.common.metric.call_llm_judge). The judge
    model defaults to BEST_LLM_MODEL_NAME (the historical behaviour, and still correct whenever an
    eval's summariser BEST model is the one being judged against a fixed baseline). Set
    JUDGE_LLM_MODEL_NAME to pin the judge to a specific model independently of BEST_LLM_MODEL_NAME
    - required for experiments that change BEST_LLM_MODEL_NAME itself (e.g. an all-luna summariser
    run), where judging with the same model being evaluated would confound the comparison.
    """
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

    judge_model = resolve_judge_model_name(settings.BEST_LLM_MODEL_NAME)

    return AzureAPIMModelAdapter(
        url=settings.AZURE_APIM_URL,
        model=judge_model,
        api_version=settings.AZURE_APIM_API_VERSION,
        token_provider=AzureStaticTokenProvider(settings.AZURE_APIM_ACCESS_TOKEN),
        subscription_key=settings.AZURE_APIM_SUBSCRIPTION_KEY,
    )


def build_bedrock_apim_adapter() -> BedrockAPIMModelAdapter:
    """Builds Bedrock APIM model adapter from environment settings."""
    settings = get_settings()
    if not settings.AZURE_APIM_BEDROCK_URL:
        msg = "AZURE_APIM_BEDROCK_URL is required"
        raise ValueError(msg)
    if not settings.AZURE_APIM_ACCESS_TOKEN:
        msg = "AZURE_APIM_ACCESS_TOKEN is required"
        raise ValueError(msg)
    if not settings.AZURE_APIM_SUBSCRIPTION_KEY:
        msg = "AZURE_APIM_SUBSCRIPTION_KEY is required"
        raise ValueError(msg)

    return BedrockAPIMModelAdapter(
        url=settings.AZURE_APIM_BEDROCK_URL,
        model=settings.BEST_LLM_MODEL_NAME,
        token_provider=AzureStaticTokenProvider(settings.AZURE_APIM_ACCESS_TOKEN),
        subscription_key=settings.AZURE_APIM_SUBSCRIPTION_KEY,
    )
