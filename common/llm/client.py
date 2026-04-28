from enum import Enum, auto

from google.genai.types import (
    GenerateContentConfig,
)
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from common.llm.adapters import AzureAPIMModelAdapter, GeminiModelAdapter, ModelAdapter, OpenAIModelAdapter
from common.llm.adapters.azure_apim import (
    AzureStaticTokenProvider,
    AzureTokenProvider,
    get_azure_client_secret_token_provider,
)
from common.prompts import get_hallucination_detection_messages
from common.settings import get_settings
from common.types import LLMHallucination, LLMHallucinationList

settings = get_settings()


class ChatBot:
    """
    Represents an interface for engaging in conversational AI tasks, including general chat,
    structured interactions, and hallucination detection.

    This class provides methods for interacting with an underlying model adapter to perform various
    chat functionalities. It includes support for retry mechanisms to ensure robust performance in
    case of failures, with methods optimized for both general conversation and specific structured
    responses. The hallucination detection method is available for examining the accuracy of responses.

    Attributes:
        adapter (ModelAdapter): The underlying adapter interface that handles communication
            with the conversational model(s).
    """

    def __init__(self, adapter: ModelAdapter) -> None:
        self.adapter = adapter
        self.messages: list[dict[str, str]] = []

    def clear_history(self) -> None:
        self.messages = []

    async def hallucination_check(self) -> list[LLMHallucination]:
        if settings.HALLUCINATION_CHECK:
            result = await self.structured_chat(
                messages=get_hallucination_detection_messages(), response_format=LLMHallucinationList
            )
            return result.hallucinations
        return []

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def chat(self, messages: list[dict[str, str]]) -> str:
        response = await self.adapter.chat(messages=self.messages + messages)
        self.messages.extend(messages)
        self.messages.append({"role": "assistant", "content": response})
        return response

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def structured_chat[T: BaseModel](self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        response = await self.adapter.structured_chat(messages=messages, response_format=response_format)
        self.messages.extend(messages)
        self.messages.append({"role": "assistant", "content": response.model_dump_json()})
        return response


def _build_azure_apim_token_provider() -> AzureTokenProvider:
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


def create_chatbot(model_type: str, model_name: str, temperature: float) -> ChatBot:
    """
    Creates and returns a chatbot instance based on the specified model type and name.

    This function initializes a ChatBot instance by selecting the appropriate model adapter
    based on the provided model type. It supports "openai", "ollama" and "gemini" model types. Additional
    settings required for model initialization are sourced from application settings or passed
    as keyword arguments. If an unsupported model type is specified, a ValueError is raised.

    Args:
        model_type: A string specifying the type of the model. Supported values are "openai",
            "ollama" and "gemini".
        model_name: A string indicating the name of the model to be used.
        **kwargs: Additional keyword arguments to be passed to the model api call, if required.

    Returns:
        ChatBot: An instance of the ChatBot class configured with the appropriate model adapter.

    Raises:
        ValueError: If the specified model type is unsupported.
    """
    if model_type == "openai":
        if not settings.AZURE_OPENAI_API_KEY:
            msg = "AZURE_OPENAI_API_KEY is required for openai model"
            raise ValueError(msg)
        if not settings.AZURE_OPENAI_API_VERSION:
            msg = "AZURE_OPENAI_API_VERSION is required for openai model"
            raise ValueError(msg)
        if not settings.AZURE_DEPLOYMENT:
            msg = "AZURE_DEPLOYMENT is required for openai model"
            raise ValueError(msg)
        if not settings.AZURE_OPENAI_ENDPOINT:
            msg = "AZURE_OPENAI_ENDPOINT is required for openai model"
            raise ValueError(msg)

        return ChatBot(
            OpenAIModelAdapter(
                model=model_name,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_deployment=settings.AZURE_DEPLOYMENT,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                temperature=temperature,
            )
        )
    elif model_type == "ollama":
        from common.llm.adapters.ollama import OllamaModelAdapter

        return ChatBot(
            OllamaModelAdapter(
                model=model_name,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=temperature,
            )
        )
    elif model_type == "azure_apim":
        if not settings.AZURE_APIM_URL:
            msg = "AZURE_APIM_URL is required for azure_apim model"
            raise ValueError(msg)
        if not settings.AZURE_APIM_API_VERSION:
            msg = "AZURE_APIM_API_VERSION is required for azure_apim model"
            raise ValueError(msg)
        if not settings.AZURE_APIM_SUBSCRIPTION_KEY:
            msg = "AZURE_APIM_SUBSCRIPTION_KEY is required for azure_apim model"
            raise ValueError(msg)

        token_provider = _build_azure_apim_token_provider()

        return ChatBot(
            AzureAPIMModelAdapter(
                url=settings.AZURE_APIM_URL,
                model=model_name,
                api_version=settings.AZURE_APIM_API_VERSION,
                token_provider=token_provider,
                subscription_key=settings.AZURE_APIM_SUBSCRIPTION_KEY,
            )
        )
    elif model_type == "gemini":
        return ChatBot(
            GeminiModelAdapter(
                model=model_name,
                generate_content_config=GenerateContentConfig(
                    safety_settings=GeminiModelAdapter.no_safety_settings(),
                    temperature=temperature,
                ),
            )
        )
    else:
        msg = f"Unsupported model type: {model_type}"
        raise ValueError(msg)


class FastOrBestLLM(Enum):
    FAST = auto()
    BEST = auto()


def create_default_chatbot(fast_or_best: FastOrBestLLM) -> ChatBot:
    """Helper function to create a chatbot client. Let's replace when we have something like OmegaConf/Hydra.cc to
    instantiate chatbot"""
    if fast_or_best == FastOrBestLLM.BEST:
        return create_chatbot(settings.BEST_LLM_PROVIDER, settings.BEST_LLM_MODEL_NAME, temperature=0.0)
    else:
        return create_chatbot(settings.FAST_LLM_PROVIDER, settings.FAST_LLM_MODEL_NAME, temperature=0.0)
