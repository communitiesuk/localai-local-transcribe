from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable

from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice

from .base import ModelAdapter
from .llm_constants import MAX_TOKENS, TEMPERATURE
from .message_utils import convert_to_openai_message

logger = logging.getLogger(__name__)

MAX_RETRIES = 6


class AzureAPIMModelAdapter(ModelAdapter):
    def __init__(
        self,
        url: str,
        model: str,
        api_version: str,
        access_token: str,
        subscription_key: str,
    ) -> None:
        self._model = model
        self._api_version = api_version
        self.async_apim_client = AsyncOpenAI(
            base_url=url + self._model,
            api_key=access_token,
            default_headers={
                "Ocp-Apim-Subscription-Key": subscription_key,
            },
            max_retries=0,
        )

    async def structured_chat[T](self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        openai_messages = [convert_to_openai_message(msg) for msg in messages]
        response = await self._call_with_retry(
            lambda: self.async_apim_client.beta.chat.completions.parse(
                model=self._model,
                messages=openai_messages,
                response_format=response_format,
                extra_query={"api-version": self._api_version},
            ),
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
        response = await self._call_with_retry(
            lambda: self.async_apim_client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                extra_query={"api-version": self._api_version},
            ),
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