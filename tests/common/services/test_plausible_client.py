from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from common.services.plausible_client import PlausibleClient


def test_send_event_posts_the_event_to_the_configured_site():
    client = PlausibleClient(domain="local-transcribe.test", host="https://plausible.test/")

    with patch("common.services.plausible_client.httpx.post") as post:
        client.send_event("summary_received", "11111111-1111-1111-1111-111111111111")

    assert post.call_args.args[0] == "https://plausible.test/api/event"
    payload = post.call_args.kwargs["json"]
    assert payload["domain"] == "local-transcribe.test"
    assert payload["name"] == "summary_received"
    assert payload["props"] == {"organisation_id": "11111111-1111-1111-1111-111111111111"}


def test_send_event_sends_no_properties_when_there_is_no_organisation():
    client = PlausibleClient(domain="local-transcribe.test", host="https://plausible.test")

    with patch("common.services.plausible_client.httpx.post") as post:
        client.send_event("summary_requested")

    assert "props" not in post.call_args.kwargs["json"]


@pytest.mark.asyncio
async def test_send_event_async_posts_the_event():
    client = PlausibleClient(domain="local-transcribe.test", host="https://plausible.test")
    async_client = MagicMock()
    async_client.post = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=async_client)
    context.__aexit__ = AsyncMock(return_value=False)

    with patch("common.services.plausible_client.httpx.AsyncClient", return_value=context):
        await client.send_event_async("transcript_received_for_direct_upload")

    assert async_client.post.call_args.args[0] == "https://plausible.test/api/event"
    assert async_client.post.call_args.kwargs["json"]["name"] == "transcript_received_for_direct_upload"
