from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from functools import cache
from typing import Protocol

from azure.identity.aio import ClientSecretCredential
from openai import APIConnectionError, APIError, AsyncOpenAI, AuthenticationError, RateLimitError
from openai.types.chat import ChatCompletion, ParsedChatCompletion
from openai.types.chat.chat_completion import Choice

from .base import ModelAdapter
from .llm_constants import MAX_TOKENS, TEMPERATURE
from .message_utils import convert_to_openai_message

logger = logging.getLogger(__name__)

MAX_RETRIES = 6


@cache
def get_azure_client_secret_token_provider(
    tenant_id: str, client_id: str, client_secret: str, scope: str
) -> AzureTokenProvider:
    """
    Returns an AzureClientSecretTokenProvider instance for the configured tenant/client. Caches providers.
    """
    return AzureClientSecretCredentialTokenProvider(tenant_id, client_id, client_secret, scope)


class AzureTokenProvider(Protocol):
    async def get_token(self) -> str: ...
    async def invalidate_token(self) -> None: ...


class AzureStaticTokenProvider:
    """
    Basic token provider which always returns the token it was initialised with
    """

    def __init__(self, token: str) -> None:
        self._token = token

    async def get_token(self) -> str:
        return self._token

    async def invalidate_token(self) -> None:
        pass


class AzureClientSecretCredentialTokenProvider:
    """
    Handles getting Azure Tokens via ClientSecretCredential
    """

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, scope: str) -> None:
        self._refresh_lock = asyncio.Lock()
        self._token: str | None = None
        self._token_valid: bool = False
        self._azure_credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        self.scope = scope

    async def _refresh_token(self) -> str:
        async with self._refresh_lock:
            if self._token_valid and self._token:
                return self._token
            result = await self._azure_credential.get_token(self.scope)
            self._token = result.token
            self._token_valid = True
            return self._token

    async def get_token(self) -> str:
        if self._token_valid and self._token:
            return self._token
        return await self._refresh_token()

    async def invalidate_token(self) -> None:
        self._token_valid = False


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
        self._cached_async_apim_client: AsyncOpenAI | None = None

    async def _get_apim_client(self) -> AsyncOpenAI:
        token = await self._token_provider.get_token()
        if self._cached_async_apim_client is None or self._cached_async_apim_client.api_key != token:
            self._cached_async_apim_client = AsyncOpenAI(
                base_url=self._url + self._model,  # APIM URL expects model here
                api_key=token,
                default_headers={
                    "Ocp-Apim-Subscription-Key": self._subscription_key,
                },
                max_retries=0,
            )
        return self._cached_async_apim_client

    async def structured_chat[T](self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        openai_messages = [convert_to_openai_message(msg) for msg in messages]

        async def call() -> ParsedChatCompletion[T]:
            client = await self._get_apim_client()
            return await client.beta.chat.completions.parse(
                model=self._model,
                messages=openai_messages,
                response_format=response_format,
                extra_query={"api-version": self._api_version},
            )

        response = await self._call_with_retry(
            call,
            "structured_chat",
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            msg = "Azure APIM response.parsed is None"
            raise ValueError(msg)
        if not isinstance(parsed, response_format):
            msg = f"Azure APIM parsed response is not of type {response_format}"
            raise TypeError(msg)
        return parsed

    async def chat(self, messages: list[dict[str, str]]) -> str:
        openai_messages = [convert_to_openai_message(msg) for msg in messages]

        async def call() -> ChatCompletion:
            client = await self._get_apim_client()
            return await client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                extra_query={"api-version": self._api_version},
            )

        response = await self._call_with_retry(
            call,
            "chat",
        )
        choice = response.choices[0]
        self.choice_incomplete(choice, response)
        message_content = choice.message.content
        if message_content is None:
            msg = "Azure APIM message.content is None"
            raise ValueError(msg)
        if not isinstance(message_content, str):
            msg = f"Azure APIM message.content is not a string: {type(message_content)}"
            raise TypeError(msg)
        return message_content

    async def _call_with_retry[T_Response](
        self, api_call: Callable[[], Awaitable[T_Response]], method_name: str
    ) -> T_Response:
        for attempt in range(MAX_RETRIES):
            try:
                response = await api_call()
                logger.info("%s - request successful", method_name)
                return response
            except RateLimitError as e:
                wait_time = self._extract_retry_after(e)
                logger.warning(
                    "%s - rate limit hit (attempt %d/%d), waiting %ds",
                    method_name,
                    attempt + 1,
                    MAX_RETRIES,
                    wait_time,
                )
                if attempt == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(wait_time)
            except AuthenticationError:
                logger.warning(
                    "%s - authentication error, refreshing token and retrying (attempt %d/%d)",
                    method_name,
                    attempt + 1,
                    MAX_RETRIES,
                )
                await self._token_provider.invalidate_token()
                self._cached_async_apim_client = await self._get_apim_client()
                if attempt == MAX_RETRIES - 1:
                    raise
            except (APIConnectionError, APIError) as e:
                logger.error("%s - %s: %s", method_name, type(e).__name__, str(e))
                raise
        msg = f"{method_name} - max retries exhausted"
        raise RuntimeError(msg)

    @staticmethod
    def _extract_retry_after(error: RateLimitError) -> int:
        retry_after_header = getattr(error.response, "headers", {}).get("Retry-After")
        if retry_after_header:
            try:
                return int(retry_after_header)
            except ValueError:
                logger.warning("Could not parse Retry-After header: %s", retry_after_header)

        error_message = str(error)
        match = re.search(r"(?:Please )?retry after (\d+) second", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))

        logger.warning("Could not extract retry-after from error, using default 60 seconds")
        return 60

    @staticmethod
    def choice_incomplete(choice: Choice, response: ChatCompletion) -> bool:
        if choice.finish_reason == "length":
            logger.warning("max output tokens reached (response_id=%s)", response.id)
            return True
        return False