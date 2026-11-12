from __future__ import annotations

import asyncio
from typing import Any

import pytest

from common.services.exceptions import TranscriptionFailedError
from common.services.transcription_services import azure
from common.services.transcription_services.azure import AzureSpeechAdapter


class FakeResponse:
    status_code = 200

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def json(self) -> dict[str, Any]:
        return self.payload

    def raise_for_status(self) -> None:
        return None


class FakeClient:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def post(self, *_args, **_kwargs):
        return FakeResponse(self.payload)


@pytest.fixture
def audio_file(tmp_path):
    path = tmp_path / "audio.wav"
    path.write_bytes(b"not really audio")
    return path


def _patch_azure(monkeypatch, payload: dict[str, Any]) -> None:
    async def fake_make_stt_request(make_request, **_kwargs):
        return await make_request({})

    monkeypatch.setattr(azure.httpx, "AsyncClient", lambda **_kwargs: FakeClient(payload))
    monkeypatch.setattr(azure, "make_stt_request", fake_make_stt_request)


def test_start_returns_an_empty_transcript_when_there_is_no_speech(monkeypatch, audio_file):
    _patch_azure(monkeypatch, {"phrases": []})

    result = asyncio.run(AzureSpeechAdapter.start(audio_file))

    assert result.transcript == []


def test_start_still_fails_when_the_response_has_no_phrases_key(monkeypatch, audio_file):
    _patch_azure(monkeypatch, {"duration": 1000})

    with pytest.raises(TranscriptionFailedError, match="No transcription phrases found in response"):
        asyncio.run(AzureSpeechAdapter.start(audio_file))


def test_start_converts_phrases_into_dialogue_entries(monkeypatch, audio_file):
    _patch_azure(
        monkeypatch,
        {
            "phrases": [
                {
                    "speaker": 1,
                    "offsetMilliseconds": 1000,
                    "durationMilliseconds": 500,
                    "text": "hello",
                }
            ]
        },
    )

    result = asyncio.run(AzureSpeechAdapter.start(audio_file))

    assert result.transcript is not None
    assert result.transcript[0]["text"] == "hello"
