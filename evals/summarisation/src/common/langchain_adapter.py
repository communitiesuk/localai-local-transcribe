from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict, Field

from common.llm.adapters.base import ModelAdapter


def _convert_message_to_dict(message: BaseMessage) -> dict[str, str]:
    """Converts LangChain message to dictionary format."""
    role = "user" if message.type == "human" else message.type
    return {"role": role, "content": str(message.content)}


class LangChainModelAdapter(BaseChatModel):
    """LangChain chat model adapter wrapping ModelAdapter."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    adapter: Any = Field(default=None)
    model_name: str = Field(default="")

    def __init__(self, adapter: ModelAdapter, model_name: str, **kwargs: Any) -> None:
        """Initializes LangChain adapter with model adapter."""
        super().__init__(**kwargs)
        self.adapter = adapter
        self.model_name = model_name

    def _generate(  # type: ignore[override]
        self,
        messages: list[BaseMessage],
        _stop: list[str] | None = None,
        _run_manager: CallbackManagerForLLMRun | None = None,
        **_kwargs: Any,
    ) -> ChatResult:
        """Generates chat response from messages using wrapped adapter."""
        message_dicts = [_convert_message_to_dict(m) for m in messages]

        try:
            asyncio.get_running_loop()
            # Already inside a running event loop — submit to a thread to avoid deadlock
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self.adapter.chat(message_dicts))
                response = future.result()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.adapter.chat(message_dicts))

        message = AIMessage(content=response)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "langchain_model_adapter"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model_name": self.model_name}
