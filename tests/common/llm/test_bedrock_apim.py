from unittest.mock import AsyncMock, MagicMock, patch

import httpx2
import pytest
from anthropic import APIConnectionError, AuthenticationError, BadRequestError, RateLimitError
from pydantic import BaseModel

from common.llm.adapters.bedrock_apim import BedrockAPIMModelAdapter
from common.llm.adapters.llm_constants import STRUCTURED_OUTPUT_TOOL_NAME

_MODULE = "common.llm.adapters.bedrock_apim"


class House(BaseModel):
    color: str
    bedrooms: int


def _text_message(text: str, stop_reason: str = "end_turn") -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    message = MagicMock()
    message.id = "msg_1"
    message.content = [block]
    message.stop_reason = stop_reason
    return message


def _tool_use_message(
    tool_input: dict, stop_reason: str = "tool_use", tool_name: str = STRUCTURED_OUTPUT_TOOL_NAME
) -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input
    message = MagicMock()
    message.id = "msg_2"
    message.content = [block]
    message.stop_reason = stop_reason
    return message


def _error_response(status_code: int, headers: dict[str, str] | None = None) -> httpx2.Response:
    request = httpx2.Request("POST", "https://example.com/v1/messages")
    return httpx2.Response(status_code, headers=headers or {}, request=request)


@pytest.fixture
def mock_token_provider():
    provider = AsyncMock()
    provider.get_token = AsyncMock(return_value="token-1")
    provider.invalidate_token = AsyncMock()
    return provider


def _make_adapter(token_provider) -> BedrockAPIMModelAdapter:
    return BedrockAPIMModelAdapter(
        url="https://apim.example.com/localtranscribe/",
        model="haiku-4-5",
        subscription_key="sub-key",
        token_provider=token_provider,
    )


@pytest.mark.asyncio
async def test_chat_builds_client_with_expected_base_url_and_headers(mock_token_provider):
    adapter = _make_adapter(mock_token_provider)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=_text_message("Hello there"))

    with patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client) as mock_cls:
        result = await adapter.chat([{"role": "user", "content": "Hi"}])

    assert result == "Hello there"
    _, kwargs = mock_cls.call_args
    assert kwargs["base_url"] == "https://apim.example.com/localtranscribe/haiku-4-5/bedrock"
    assert kwargs["auth_token"] == "token-1"  # noqa: S105 - test fixture token, not a real secret
    assert kwargs["default_headers"] == {"Ocp-Apim-Subscription-Key": "sub-key"}


@pytest.mark.asyncio
async def test_chat_splits_system_message_and_passes_model(mock_token_provider):
    adapter = _make_adapter(mock_token_provider)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=_text_message("response"))

    with patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client):
        await adapter.chat(
            [
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Hi"},
            ]
        )

    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["model"] == "haiku-4-5"
    assert kwargs["system"] == "Be concise."
    assert kwargs["messages"] == [{"role": "user", "content": "Hi"}]


@pytest.mark.asyncio
async def test_chat_raises_if_no_text_block(mock_token_provider):
    adapter = _make_adapter(mock_token_provider)

    message = MagicMock()
    message.content = []
    message.stop_reason = "end_turn"

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=message)

    with patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client), pytest.raises(ValueError, match="text"):
        await adapter.chat([{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_chat_logs_warning_on_max_tokens_stop_reason(mock_token_provider, caplog):
    adapter = _make_adapter(mock_token_provider)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=_text_message("cut off", stop_reason="max_tokens"))

    with patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client), caplog.at_level("WARNING"):
        result = await adapter.chat([{"role": "user", "content": "Hi"}])

    assert result == "cut off"
    assert any("max output tokens" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_structured_chat_forces_tool_use_and_parses_input(mock_token_provider):
    adapter = _make_adapter(mock_token_provider)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value=_tool_use_message({"color": "red", "bedrooms": 3}),
    )

    with patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client):
        result = await adapter.structured_chat([{"role": "user", "content": "Describe the house"}], House)

    assert result == House(color="red", bedrooms=3)
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["tool_choice"] == {"type": "tool", "name": STRUCTURED_OUTPUT_TOOL_NAME}
    assert kwargs["tools"][0]["name"] == STRUCTURED_OUTPUT_TOOL_NAME
    assert kwargs["tools"][0]["input_schema"] == House.model_json_schema()


@pytest.mark.asyncio
async def test_structured_chat_raises_if_no_tool_use_block(mock_token_provider):
    adapter = _make_adapter(mock_token_provider)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=_text_message("no tool call"))

    with patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client), pytest.raises(ValueError, match="tool_use"):
        await adapter.structured_chat([{"role": "user", "content": "Describe the house"}], House)


@pytest.mark.asyncio
async def test_rate_limit_error_is_retried_respecting_retry_after(mock_token_provider):
    adapter = _make_adapter(mock_token_provider)

    rate_limit_error = RateLimitError("rate limited", response=_error_response(429, {"Retry-After": "0"}), body=None)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=[rate_limit_error, _text_message("ok")])

    with patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client), patch(f"{_MODULE}.asyncio.sleep", AsyncMock()):
        result = await adapter.chat([{"role": "user", "content": "Hi"}])

    assert result == "ok"
    assert mock_client.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_authentication_error_invalidates_token_and_retries(mock_token_provider):
    mock_token_provider.get_token = AsyncMock(side_effect=["stale-token", "fresh-token", "fresh-token"])
    adapter = _make_adapter(mock_token_provider)

    auth_error = AuthenticationError("bad token", response=_error_response(401), body=None)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=[auth_error, _text_message("ok")])

    with patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client):
        result = await adapter.chat([{"role": "user", "content": "Hi"}])

    assert result == "ok"
    mock_token_provider.invalidate_token.assert_called_once()


@pytest.mark.asyncio
async def test_bad_request_error_is_not_retried(mock_token_provider):
    adapter = _make_adapter(mock_token_provider)

    bad_request_error = BadRequestError("bad request", response=_error_response(400), body=None)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=bad_request_error)

    with patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client), pytest.raises(BadRequestError):
        await adapter.chat([{"role": "user", "content": "Hi"}])

    assert mock_client.messages.create.call_count == 1


@pytest.mark.asyncio
async def test_connection_error_is_retried_then_raised(mock_token_provider):
    adapter = _make_adapter(mock_token_provider)

    request = httpx2.Request("POST", "https://example.com/v1/messages")
    connection_error = APIConnectionError(message="connection failed", request=request)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=connection_error)

    with (
        patch(f"{_MODULE}.AsyncAnthropic", return_value=mock_client),
        patch(f"{_MODULE}.asyncio.sleep", AsyncMock()),
        pytest.raises(APIConnectionError),
    ):
        await adapter.chat([{"role": "user", "content": "Hi"}])

    assert mock_client.messages.create.call_count == 6
