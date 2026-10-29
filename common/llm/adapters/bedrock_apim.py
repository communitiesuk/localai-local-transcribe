from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

from anthropic import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncAnthropic,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    omit,
)
from anthropic.types import Message, ToolChoiceToolParam, ToolParam
from pydantic import BaseModel

from common.apim_auth import AzureTokenProvider

from .base import ModelAdapter
from .llm_constants import MAX_COMPLETION_TOKENS, STRUCTURED_OUTPUT_TOOL_NAME
from .message_utils import convert_to_anthropic_messages

logger = logging.getLogger(__name__)

MAX_RETRIES = 6


class BedrockAPIMModelAdapter(ModelAdapter):
    """Model adapter for AWS Bedrock models (e.g. Claude Haiku/Sonnet) accessed through Azure APIM's
    "localtranscribe" product, which fronts Bedrock via an Anthropic-Messages-API-shaped gateway
    (`.../{model}/bedrock/v1/messages`)."""

    def __init__(
        self,
        url: str,
        model: str,
        subscription_key: str,
        token_provider: AzureTokenProvider,
    ) -> None:
        self._model = model
        self._url = url
        self._subscription_key = subscription_key
        self._token_provider = token_provider
        self._cached_async_apim_client: AsyncAnthropic | None = None
        self._cached_token: str | None = None

    async def _get_apim_client(self) -> AsyncAnthropic:
        logger.info("BEDROCK APIM CLIENT: retrieving APIM client token")

        token = await self._token_provider.get_token()

        if self._cached_async_apim_client is None or self._cached_token != token:
            logger.info("BEDROCK APIM CLIENT: creating new AsyncAnthropic client")

            self._cached_token = token
            self._cached_async_apim_client = AsyncAnthropic(
                base_url=self._url + self._model + "/bedrock",
                auth_token=token,
                default_headers={
                    "Ocp-Apim-Subscription-Key": self._subscription_key,
                },
                max_retries=0,
            )

        return self._cached_async_apim_client

    async def chat(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        system, anthropic_messages = convert_to_anthropic_messages(messages)

        async def call() -> Message:
            client = await self._get_apim_client()

            return await client.messages.create(
                model=self._model,
                max_tokens=MAX_COMPLETION_TOKENS,
                messages=anthropic_messages,
                system=system if system is not None else omit,
            )

        logger.info("BEDROCK APIM REQUEST: chat")

        response = await self._call_with_retry(call, "chat")

        self.log_if_stop_reason_is_max_tokens(response)

        text = self._extract_text(response)

        logger.info("BEDROCK APIM SUCCESS: chat")

        return text

    async def structured_chat[T: BaseModel](
        self,
        messages: list[dict[str, str]],
        response_format: type[T],
    ) -> T:
        system, anthropic_messages = convert_to_anthropic_messages(messages)

        tool = ToolParam(
            name=STRUCTURED_OUTPUT_TOOL_NAME,
            input_schema=response_format.model_json_schema(),
        )
        tool_choice = ToolChoiceToolParam(type="tool", name=STRUCTURED_OUTPUT_TOOL_NAME)

        async def call() -> Message:
            client = await self._get_apim_client()

            return await client.messages.create(
                model=self._model,
                max_tokens=MAX_COMPLETION_TOKENS,
                messages=anthropic_messages,
                tools=[tool],
                tool_choice=tool_choice,
                system=system if system is not None else omit,
            )

        logger.info("BEDROCK APIM REQUEST: structured_chat")

        response = await self._call_with_retry(call, "structured_chat")

        self.log_if_stop_reason_is_max_tokens(response)

        tool_input = self._extract_tool_input(response, STRUCTURED_OUTPUT_TOOL_NAME)

        logger.info("BEDROCK APIM SUCCESS: structured_chat")

        return response_format.model_validate(tool_input)

    @staticmethod
    def _extract_text(response: Message) -> str:
        for block in response.content:
            if block.type == "text":
                text = block.text

                if not isinstance(text, str) or not text:
                    error_msg = "Bedrock APIM response text block has empty/non-string text"

                    logger.error("BEDROCK APIM FAILURE: chat - %s", error_msg)

                    raise ValueError(error_msg)

                return text

        error_msg = "Bedrock APIM response did not contain a text content block"

        logger.error("BEDROCK APIM FAILURE: chat - %s", error_msg)

        raise ValueError(error_msg)

    @staticmethod
    def _extract_tool_input(response: Message, tool_name: str) -> dict[str, Any]:
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return block.input

        error_msg = "Bedrock APIM response did not contain the expected tool_use block"

        logger.error("BEDROCK APIM FAILURE: structured_chat - %s", error_msg)

        raise ValueError(error_msg)

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
                    "BEDROCK APIM RETRY: %s - rate limit hit (attempt %d/%d), retrying in %ds",
                    method_name,
                    attempt + 1,
                    MAX_RETRIES,
                    wait_time,
                )

                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        "BEDROCK APIM FAILURE: %s - max retries exceeded due to rate limiting",
                        method_name,
                    )
                    raise

                await asyncio.sleep(wait_time)

            except AuthenticationError:
                logger.warning(
                    "BEDROCK APIM RETRY: %s - authentication error, refreshing token and retrying (attempt %d/%d)",
                    method_name,
                    attempt + 1,
                    MAX_RETRIES,
                )

                await self._token_provider.invalidate_token()

                self._cached_async_apim_client = await self._get_apim_client()

                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        "BEDROCK APIM FAILURE: %s - max retries exceeded due to authentication errors",
                        method_name,
                    )
                    raise

            except BadRequestError:
                # A 400 (e.g. a content-safety filter rejecting the request) is a definitive,
                # deterministic rejection of this exact request — retrying it identically would
                # only waste time on a call that will fail the same way every time.
                logger.warning("BEDROCK APIM FAILURE: %s - BadRequestError is not retryable", method_name)
                raise

            except (APIConnectionError, APIError, APITimeoutError) as error:
                logger.warning(
                    "BEDROCK APIM RETRY: %s - %s: %s (attempt %d/%d)",
                    method_name,
                    type(error).__name__,
                    str(error),
                    attempt + 1,
                    MAX_RETRIES,
                )

                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        "BEDROCK APIM FAILURE: %s - %s after maximum retries: %s",
                        method_name,
                        type(error).__name__,
                        str(error),
                    )
                    raise

        error_msg = f"{method_name} - maximum retries exhausted"

        logger.error("BEDROCK APIM FAILURE: %s", error_msg)

        raise RuntimeError(error_msg)

    @staticmethod
    def _extract_retry_after(error: RateLimitError) -> int:
        retry_after_header = getattr(error.response, "headers", {}).get("Retry-After")

        if retry_after_header:
            try:
                return int(retry_after_header)

            except ValueError:
                logger.warning(
                    "BEDROCK APIM WARNING: failed to parse Retry-After header: %s",
                    retry_after_header,
                )

        error_message = str(error)

        match = re.search(
            r"(?:Please )?retry after (\d+) second",
            error_message,
            re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

        logger.warning("BEDROCK APIM WARNING: could not determine retry-after value, defaulting to 60 seconds")

        return 60

    @staticmethod
    def log_if_stop_reason_is_max_tokens(response: Message) -> None:
        if response.stop_reason == "max_tokens":
            logger.warning(
                "BEDROCK APIM WARNING: max output tokens reached (response_id=%s)",
                response.id,
            )
