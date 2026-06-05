from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import Any

import dspy
import litellm

from common.llm.adapters.base import ModelAdapter

logger = logging.getLogger(__name__)


class DSPyModelAdapterWrapper(dspy.BaseLM):
    """Wraps ModelAdapter for use with DSPy framework."""

    def __init__(self, adapter: ModelAdapter, model_name: str, **kwargs: Any) -> None:
        """Initializes DSPy wrapper with model adapter."""
        super().__init__(model=model_name, **kwargs)
        self.adapter = adapter
        self.wrapper_history: list[dict[str, Any]] = []

    def forward(
        self,
        prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> litellm.ModelResponse:
        """Calls model adapter with prompt or messages and returns an OpenAI-compatible response."""
        if messages is None and prompt is None:
            msg = "Either prompt or messages must be provided"
            raise ValueError(msg)

        if messages is None:
            messages = [{"role": "user", "content": prompt or ""}]

        try:
            asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.adapter.chat(messages))
                text = future.result()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            text = loop.run_until_complete(self.adapter.chat(messages))

        self.wrapper_history.append(
            {
                "messages": messages,
                "response": text,
                "kwargs": kwargs,
            }
        )

        return litellm.ModelResponse(
            choices=[litellm.utils.Choices(message=litellm.utils.Message(content=text, role="assistant"))],
            model=self.model,
        )

    def inspect_history(self, n: int = 1) -> list[dict[str, Any]]:
        """Returns last n entries from call history."""
        return self.wrapper_history[-n:] if self.wrapper_history else []
