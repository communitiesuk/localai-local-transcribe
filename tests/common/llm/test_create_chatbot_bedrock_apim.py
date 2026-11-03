from unittest.mock import MagicMock, patch

import pytest

from common.llm.adapters import BedrockAPIMModelAdapter
from common.llm.client import create_chatbot

_MODULE = "common.llm.client"


def test_create_chatbot_raises_without_bedrock_url():
    with patch(f"{_MODULE}.settings") as mock_settings:
        mock_settings.AZURE_APIM_BEDROCK_URL = None
        mock_settings.AZURE_APIM_SUBSCRIPTION_KEY = "sub-key"

        with pytest.raises(ValueError, match="AZURE_APIM_BEDROCK_URL"):
            create_chatbot("bedrock_apim", "haiku-4-5", temperature=0.0)


def test_create_chatbot_raises_without_subscription_key():
    with patch(f"{_MODULE}.settings") as mock_settings:
        mock_settings.AZURE_APIM_BEDROCK_URL = "https://apim.example.com/localtranscribe/"
        mock_settings.AZURE_APIM_SUBSCRIPTION_KEY = None

        with pytest.raises(ValueError, match="AZURE_APIM_SUBSCRIPTION_KEY"):
            create_chatbot("bedrock_apim", "haiku-4-5", temperature=0.0)


def test_create_chatbot_builds_bedrock_apim_adapter():
    with (
        patch(f"{_MODULE}.settings") as mock_settings,
        patch(f"{_MODULE}.build_apim_token_provider", return_value=MagicMock()) as mock_build_token_provider,
    ):
        mock_settings.AZURE_APIM_BEDROCK_URL = "https://apim.example.com/localtranscribe/"
        mock_settings.AZURE_APIM_SUBSCRIPTION_KEY = "sub-key"

        chatbot = create_chatbot("bedrock_apim", "haiku-4-5", temperature=0.0)

    mock_build_token_provider.assert_called_once()
    assert isinstance(chatbot.adapter, BedrockAPIMModelAdapter)
    adapter = chatbot.adapter
    assert adapter._model == "haiku-4-5"  # noqa: SLF001 - verifying wiring through to adapter constructor args
    assert adapter._url == "https://apim.example.com/localtranscribe/"  # noqa: SLF001
    assert adapter._subscription_key == "sub-key"  # noqa: SLF001
