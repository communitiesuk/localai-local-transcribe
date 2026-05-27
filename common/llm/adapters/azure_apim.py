from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable

# Import the synchronous OpenAI client instead of AsyncOpenAI
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)
from openai.types.chat import ChatCompletion, ParsedChatCompletion
from openai.types.chat.chat_completion import Choice

from common.azure_apim_auth import AzureTokenProvider
from common.settings import get_settings

from .base import ModelAdapter
from .llm_constants import BEST_LLM_TEMPERATURE, FAST_LLM_TEMPERATURE, MAX_COMPLETION_TOKENS
from .message_utils import convert_to_openai_message

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_RETRIES = 6


class AzureAPIMModelAdapter(ModelAdapter):
    def __init__(
        self,
        url: str,
        model: str,
        api_version: str,
        subscription_key: str,
        token_provider: AzureTokenProvider,
    ) -> None:
        self._model = model
        self._api_version = api_version
        self._url = url
        self._subscription_key = subscription_key
        self._token_provider = token_provider
        self._cached_apim_client: OpenAI | None = None

    async def _get_apim_client(self) -> OpenAI:
        logger.info("APIM CLIENT: retrieving APIM client token")

        # We fetch the token asynchronously since the provider is async
        token = await self._token_provider.get_token()

        if self._cached_apim_client is None or self._cached_apim_client.api_key != token:
            logger.info("APIM CLIENT: creating new OpenAI client")

            # We instantiate the synchronous client. No event loops are registered,
            # which permanently eliminates any "Event loop is closed" warnings.
            self._cached_apim_client = OpenAI(
                base_url=self._url + self._model,
                api_key=token,
                default_headers={
                    "Ocp-Apim-Subscription-Key": self._subscription_key,
                },
                max_retries=0,
            )

        return self._cached_apim_client

    async def structured_chat[T](
        self,
        messages: list[dict[str, str]],
        response_format: type[T],
    ) -> T:
        openai_messages = [convert_to_openai_message(msg) for msg in messages]

        # The call is technically wrapped in an async def to match the interface,
        # but the network operation runs synchronously and safely.
        async def call() -> ParsedChatCompletion[T]:
            client = await self._get_apim_client()

            return client.beta.chat.completions.parse(
                model=self._model,
                messages=openai_messages,
                response_format=response_format,
                extra_query={"api-version": self._api_version},
            )

        logger.info("APIM REQUEST: structured_chat")

        response = await self._call_with_retry(
            call,
            "structured_chat",
        )

        parsed = response.choices[0].message.parsed

        if parsed is None:
            error_msg = "Azure APIM response.parsed is None"
            logger.error("APIM FAILURE: structured_chat - %s", error_msg)
            raise ValueError(error_msg)

        if not isinstance(parsed, response_format):
            error_msg = f"Azure APIM parsed response is not of type {response_format}"
            logger.error("APIM FAILURE: structured_chat - %s", error_msg)
            raise TypeError(error_msg)

        logger.info("APIM SUCCESS: structured_chat")
        return parsed

    async def chat(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        openai_messages = [convert_to_openai_message(msg) for msg in messages]

        temperature = FAST_LLM_TEMPERATURE if "gpt-5" in self._model else BEST_LLM_TEMPERATURE

        async def call() -> ChatCompletion:
            client = await self._get_apim_client()

            return client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                temperature=temperature,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                extra_query={"api-version": self._api_version},
            )

        logger.info("APIM REQUEST: chat")

        response = await self._call_with_retry(
            call,
            "chat",
        )

        choice = response.choices[0]
        self.choice_incomplete(choice, response)
        message_content = choice.message.content

        if message_content is None:
            error_msg = "Azure APIM message.content is None"
            logger.error("APIM FAILURE: chat - %s", error_msg)
            raise ValueError(error_msg)

        if not isinstance(message_content, str):
            error_msg = f"Azure APIM message.content is not a string: {type(message_content)}"
            logger.error("APIM FAILURE: chat - %s", error_msg)
            raise TypeError(error_msg)

        logger.info("APIM SUCCESS: chat")
        return message_content

    async def _call_with_retry[T_Response](
        self,
        api_call: Callable[[], Awaitable[T_Response]],
        method_name: str,
    ) -> T_Response:
        for attempt in range(MAX_RETRIES):
            try:
                return await api_call()

            except RateLimitError as error:
                wait_time = self._extract_retry_after(error)
                logger.warning(
                    "APIM RETRY: %s - rate limit hit (attempt %d/%d), retrying in %ds",
                    method_name,
                    attempt + 1,
                    MAX_RETRIES,
                    wait_time,
                )

                if attempt == MAX_RETRIES - 1:
                    logger.error("APIM FAILURE: %s - max retries exceeded due to rate limiting", method_name)
                    raise

                await asyncio.sleep(wait_time)

            except AuthenticationError:
                logger.warning(
                    "APIM RETRY: %s - authentication error, refreshing token and retrying (attempt %d/%d)",
                    method_name,
                    attempt + 1,
                    MAX_RETRIES,
                )

                await self._token_provider.invalidate_token()
                self._cached_apim_client = await self._get_apim_client()

                if attempt == MAX_RETRIES - 1:
                    logger.error("APIM FAILURE: %s - max retries exceeded due to authentication errors", method_name)
                    raise

            except (APIConnectionError, APIError, APITimeoutError) as error:
                logger.warning(
                    "APIM RETRY: %s - %s: %s (attempt %d/%d)",
                    method_name,
                    type(error).__name__,
                    str(error),
                    attempt + 1,
                    MAX_RETRIES,
                )

                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        "APIM FAILURE: %s - %s after maximum retries: %s",
                        method_name,
                        type(error).__name__,
                        str(error),
                    )
                raise

        error_msg = f"{method_name} - maximum retries exhausted"
        logger.error("APIM FAILURE: %s", error_msg)
        raise RuntimeError(error_msg)

    @staticmethod
    def _extract_retry_after(error: RateLimitError) -> int:
        retry_after_header = getattr(error.response, "headers", {}).get("Retry-After")
        if retry_after_header:
            try:
                return int(retry_after_header)
            except ValueError:
                logger.warning("APIM WARNING: failed to parse Retry-After header: %s", retry_after_header)

        error_message = str(error)
        match = re.search(r"(?:Please )?retry after (\d+) second", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))

        logger.warning("APIM WARNING: could not determine retry-after value, defaulting to 60 seconds")
        return 60

    @staticmethod
    def choice_incomplete(
        choice: Choice,
        response: ChatCompletion,
    ) -> bool:
        if choice.finish_reason == "length":
            logger.warning("APIM WARNING: max output tokens reached (response_id=%s)", response.id)
            return True
        return False
