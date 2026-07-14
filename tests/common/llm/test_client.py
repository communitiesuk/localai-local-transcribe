from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from openai import BadRequestError
from pydantic import BaseModel

from common.llm.client import ChatBot, create_chatbot
from tests.marks import costs_money

pytestmark = [costs_money]
structured_chat_prompt_1 = [
    {"role": "system", "content": "You are a helpful assistant. Extract the properties of the house."},
    {"role": "user", "content": "The house is red and ten meters tall, with 3 bedrooms and 2 bathrooms."},
]
structured_chat_prompt_2 = [
    {"role": "user", "content": "The house is blue and six meters tall, with 1 bedroom and 1 bathrooms."},
]


chat_prompts_1 = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello my name is John."},
]
chat_prompts_2 = [
    {"role": "user", "content": "My friends name is Sally"},
]
chat_prompts_3 = [
    {"role": "user", "content": "Please tell me my name and my friends name again?"},
]


class House(BaseModel):
    color: str
    size: int
    size_unit: str
    bedrooms: int
    bathrooms: int


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "model_type_and_model_name",
    [
        ("openai", "gpt-4o-2024-08-06"),
        ("gemini", "gemini-2.0-flash"),
    ],
)
async def test_structured_output_chatbots(model_type_and_model_name) -> None:
    chatbot = create_chatbot(
        model_type=model_type_and_model_name[0], model_name=model_type_and_model_name[1], temperature=0.0
    )
    expected_output_1 = House(color="red", size=10, size_unit="meters", bedrooms=3, bathrooms=2)
    result = await chatbot.structured_chat(structured_chat_prompt_1, House)
    assert result == expected_output_1
    expected_output_2 = House(color="blue", size=6, size_unit="meters", bedrooms=1, bathrooms=1)
    result = await chatbot.structured_chat(structured_chat_prompt_2, House)
    assert result == expected_output_2


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "model_type_and_model_name",
    [
        ("openai", "gpt-4o-2024-08-06"),
        ("gemini", "gemini-2.0-flash"),
    ],
)
async def test_chat_chatbots(model_type_and_model_name) -> None:
    chatbot = create_chatbot(
        model_type=model_type_and_model_name[0], model_name=model_type_and_model_name[1], temperature=0.0
    )
    result_1 = await chatbot.chat(chat_prompts_1)
    result_2 = await chatbot.chat(chat_prompts_2)
    result_3 = await chatbot.chat(chat_prompts_3)
    err_msg = f"""Failed to recall information from chat history:
    \n{chat_prompts_1}\n{result_1}\n{chat_prompts_2}\n{result_2}\n{chat_prompts_3}\n{result_3}"""

    assert "John" in result_3, err_msg
    assert "Sally" in result_3, err_msg


@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.chat = AsyncMock(return_value="default response")
    adapter.structured_chat = AsyncMock()
    return adapter


@pytest.mark.asyncio
async def test_message_history_structure(mock_adapter):
    mock_adapter.chat = AsyncMock(side_effect=["Response 1", "Response 2", "Response 3"])
    chatbot = ChatBot(adapter=mock_adapter)

    await chatbot.chat(messages=[{"role": "user", "content": "Hello"}])
    await chatbot.chat(messages=[{"role": "user", "content": "How are you?"}])
    await chatbot.chat(messages=[{"role": "user", "content": "Tell me a joke"}])

    expected = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "Response 2"},
        {"role": "user", "content": "Tell me a joke"},
        {"role": "assistant", "content": "Response 3"},
    ]
    assert chatbot.messages == expected


def _bad_request_error() -> BadRequestError:
    body = {"code": "content_filter"}
    response = httpx.Response(400, request=httpx.Request("POST", "http://x"), json={"error": body})
    return BadRequestError("content filtered", response=response, body=body)


@pytest.mark.asyncio
async def test_chat_does_not_retry_bad_request_error(mock_adapter):
    """A content-filter (or any other) BadRequestError is a deterministic rejection — retrying the
    identical request would just waste time on a call that will fail the same way every time."""
    mock_adapter.chat = AsyncMock(side_effect=_bad_request_error())
    chatbot = ChatBot(adapter=mock_adapter)

    with pytest.raises(BadRequestError):
        await chatbot.chat(messages=[{"role": "user", "content": "Hi"}])

    assert mock_adapter.chat.call_count == 1


@pytest.mark.asyncio
async def test_structured_chat_does_not_retry_bad_request_error(mock_adapter):
    mock_adapter.structured_chat = AsyncMock(side_effect=_bad_request_error())
    chatbot = ChatBot(adapter=mock_adapter)

    with pytest.raises(BadRequestError):
        await chatbot.structured_chat(messages=[{"role": "user", "content": "Hi"}], response_format=House)

    assert mock_adapter.structured_chat.call_count == 1


@pytest.mark.asyncio
async def test_chat_appends_to_message_history(mock_adapter):
    mock_adapter.chat = AsyncMock(side_effect=["Hello, I am an AI.", "Second response", "Third response"])
    chatbot = ChatBot(adapter=mock_adapter)

    await chatbot.chat(messages=[{"role": "user", "content": "Hi"}])

    expected = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello, I am an AI."},
    ]

    assert chatbot.messages == expected
