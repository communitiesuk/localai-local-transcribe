from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from evals.dataset_generation.silver_transcripts.src import pipeline as pipeline_module
from evals.dataset_generation.silver_transcripts.src.core import batch_transcription as batch_module
from evals.dataset_generation.silver_transcripts.src.pipeline import SilverTranscriptPipeline


@pytest.mark.parametrize(
    ("entries", "expected_text", "delete_fails"),
    [
        ([{"speaker": "1", "text": "hello", "start_time": 0.0, "end_time": 1.0, "confidence": 0.9}], "hello", False),
        ([], "", False),
        ([{"speaker": "1", "text": "hello", "start_time": 0.0, "end_time": 1.0, "confidence": 0.9}], "hello", True),
    ],
)
def test_azure_batch_path_uploads_polls_and_deletes_temporary_audio(
    tmp_path, monkeypatch, caplog, entries, expected_text, delete_fails
):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake audio")
    calls = {"uploads": [], "checks": 0, "deletes": []}

    class FakeStorage:
        name = "s3"

        async def upload(self, key, path):
            calls["uploads"].append((key, path))

        async def delete(self, key):
            calls["deletes"].append(key)
            if delete_fails:
                message = "storage delete failed"
                raise OSError(message)

    async def fake_start(_adapter, recording):
        assert recording.s3_file_key == calls["uploads"][0][0]
        return SimpleNamespace(job_name="job")

    async def fake_check(_adapter, _job):
        calls["checks"] += 1
        if calls["checks"] == 1:
            return SimpleNamespace(job_status="Running", transcript=None)
        return SimpleNamespace(
            job_status="Succeeded",
            transcript=entries,
        )

    monkeypatch.setattr(batch_module, "get_storage_service", lambda _name: FakeStorage())
    monkeypatch.setattr(batch_module, "BATCH_TRANSCRIPTION_POLL_SECONDS", 0)
    monkeypatch.setattr(pipeline_module.AzureBatchTranscriptionAdapter, "start", classmethod(fake_start))
    monkeypatch.setattr(pipeline_module.AzureBatchTranscriptionAdapter, "check", classmethod(fake_check))

    pipeline = SilverTranscriptPipeline(tmp_path / "work")
    result = asyncio.run(pipeline._transcribe_with_azure_batch(audio_path, 7200))  # noqa: SLF001

    assert result.text == expected_text
    if entries:
        assert result.dialogue_entries[0]["confidence"] == pytest.approx(0.9)
    assert len(calls["uploads"]) == 1
    assert calls["checks"] == 2
    assert calls["deletes"] == [calls["uploads"][0][0]]
    if delete_fails:
        assert "Could not delete temporary batch audio" in caplog.text


def test_batch_timeout_deletes_temporary_audio(tmp_path, monkeypatch):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake audio")
    calls = {"deletes": [], "checks": 0}

    class FakeStorage:
        name = "s3"

        async def upload(self, _key, _path):
            pass

        async def delete(self, key):
            calls["deletes"].append(key)

    async def fake_start(_adapter, _recording):
        return SimpleNamespace(job_name="job")

    async def fake_check(_adapter, _job):
        calls["checks"] += 1
        return SimpleNamespace(job_status="Running", transcript=None)

    monkeypatch.setattr(batch_module, "get_storage_service", lambda _name: FakeStorage())
    monkeypatch.setattr(batch_module, "MIN_BATCH_TRANSCRIPTION_TIMEOUT_SECONDS", 0)
    monkeypatch.setattr(pipeline_module.AzureBatchTranscriptionAdapter, "start", classmethod(fake_start))
    monkeypatch.setattr(pipeline_module.AzureBatchTranscriptionAdapter, "check", classmethod(fake_check))

    pipeline = SilverTranscriptPipeline(tmp_path / "work")
    with pytest.raises(TimeoutError, match="did not complete within 0 minutes"):
        asyncio.run(pipeline._transcribe_with_azure_batch(audio_path, 0))  # noqa: SLF001

    assert calls["checks"] == 0
    assert len(calls["deletes"]) == 1


def test_batch_path_rejects_local_storage_before_upload(tmp_path, monkeypatch):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake audio")

    class LocalStorage:
        name = "local"

        async def upload(self, _key, _path):
            pytest.fail("local storage must be rejected before upload")

    monkeypatch.setattr(batch_module, "get_storage_service", lambda _name: LocalStorage())
    pipeline = SilverTranscriptPipeline(tmp_path / "work")

    with pytest.raises(ValueError, match="STORAGE_SERVICE_NAME=local"):
        asyncio.run(pipeline._transcribe_with_azure_batch(audio_path, 7200))  # noqa: SLF001


def test_transcription_rejects_audio_over_batch_limit(tmp_path):
    pipeline = SilverTranscriptPipeline(tmp_path / "work")

    with pytest.raises(ValueError, match="supports up to 4 hours"):
        pipeline._transcribe(Path("audio.mp3"), pipeline_module.MAX_BATCH_TRANSCRIPTION_SECONDS + 1, True)  # noqa: SLF001
