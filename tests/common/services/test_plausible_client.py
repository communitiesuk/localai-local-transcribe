from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from common.services.plausible_client import PlausibleClient


def async_client_returning(response_client):
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response_client)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


@pytest.mark.asyncio
async def test_sends_the_browser_user_agent_and_address():
    """Plausible counts an event against the visitor's user agent and IP, and drops events that look like ours."""
    client = PlausibleClient(domain="local-transcribe.test", host="https://plausible.test")
    http = MagicMock()
    http.post = AsyncMock()

    with patch("common.services.plausible_client.httpx.AsyncClient", return_value=async_client_returning(http)):
        await client.send_event("summary_requested", None, "Mozilla/5.0", "203.0.113.7")

    headers = http.post.call_args.kwargs["headers"]
    assert headers["User-Agent"] == "Mozilla/5.0"
    assert headers["X-Forwarded-For"] == "203.0.113.7"
    assert http.post.call_args.args[0] == "https://plausible.test/api/event"


@pytest.mark.asyncio
async def test_sends_the_organisation_as_a_property():
    client = PlausibleClient(domain="local-transcribe.test", host="https://plausible.test")
    http = MagicMock()
    http.post = AsyncMock()

    with patch("common.services.plausible_client.httpx.AsyncClient", return_value=async_client_returning(http)):
        await client.send_event("audio_upload_complete_from_live_recording", "org-1", "Mozilla/5.0", "203.0.113.7")

    payload = http.post.call_args.kwargs["json"]
    assert payload["domain"] == "local-transcribe.test"
    assert payload["props"] == {"organisation_id": "org-1"}


@pytest.mark.asyncio
async def test_sends_no_properties_and_no_address_when_there_are_none():
    client = PlausibleClient(domain="local-transcribe.test", host="https://plausible.test")
    http = MagicMock()
    http.post = AsyncMock()

    with patch("common.services.plausible_client.httpx.AsyncClient", return_value=async_client_returning(http)):
        await client.send_event("summary_requested", None, "Mozilla/5.0", None)

    assert "props" not in http.post.call_args.kwargs["json"]
    assert "X-Forwarded-For" not in http.post.call_args.kwargs["headers"]
