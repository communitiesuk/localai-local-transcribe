from __future__ import annotations

import asyncio
from typing import Any

from common.services.transcription_services import azure_async
from common.services.transcription_services.azure_async import AzureBatchTranscriptionAdapter
from common.types import TranscriptionJobMessageData


def test_batch_dialogue_entries_preserve_nbest_confidence():
    entries = AzureBatchTranscriptionAdapter.get_dialogue_entries(
        {
            "recognizedPhrases": [
                {
                    "speaker": 1,
                    "offsetMilliseconds": 1000,
                    "durationMilliseconds": 500,
                    "nBest": [{"display": "hello", "confidence": "0.87"}],
                },
                {
                    "speaker": 2,
                    "offsetMilliseconds": 2000,
                    "durationMilliseconds": 500,
                    "nBest": [{"display": "there"}],
                },
            ]
        }
    )

    assert entries[0] == {
        "speaker": "1",
        "text": "hello",
        "start_time": 1.0,
        "end_time": 1.5,
        "confidence": 0.87,
    }
    assert entries[1] == {"speaker": "2", "text": "there", "start_time": 2.0, "end_time": 2.5}


def test_batch_check_marks_success_even_when_transcript_is_empty(monkeypatch):
    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict[str, Any]:
            return {"status": "Succeeded", "links": {"files": "https://files.example.test"}}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, *_args, **_kwargs):
            return FakeResponse()

    async def fake_make_stt_request(make_request, **_kwargs):
        return await make_request({})

    async def fake_get_results(_adapter, _files_url, data):
        return data.model_copy(update={"transcript": []})

    monkeypatch.setattr(azure_async.httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    monkeypatch.setattr(azure_async, "make_stt_request", fake_make_stt_request)
    monkeypatch.setattr(AzureBatchTranscriptionAdapter, "get_results", classmethod(fake_get_results))
    job = TranscriptionJobMessageData(transcription_service=AzureBatchTranscriptionAdapter.name, job_name="job")

    result = asyncio.run(AzureBatchTranscriptionAdapter.check(job, retry_count=1, retry_delay=0))

    assert result.job_status == "Succeeded"
    assert result.transcript == []
