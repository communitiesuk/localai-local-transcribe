"""Reusable Azure batch-transcription orchestration for local audio inputs."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from uuid import uuid4

from common.database.postgres_models import DialogueEntry, Recording
from common.services.storage_services import get_storage_service
from common.services.transcription_services.azure_async import AzureBatchTranscriptionAdapter
from common.settings import get_settings

logger = logging.getLogger(__name__)

BATCH_TRANSCRIPTION_POLL_SECONDS = 5
MIN_BATCH_TRANSCRIPTION_TIMEOUT_SECONDS = 1800


async def run_azure_batch_transcription(
    audio_path: Path,
    duration: float,
    *,
    key_prefix: str = "silver-transcripts",
) -> tuple[list[DialogueEntry], float]:
    """Upload audio, poll Azure batch transcription, and return transcript entries plus elapsed seconds."""
    storage_service = get_storage_service(get_settings().STORAGE_SERVICE_NAME)
    if storage_service.name == "local":
        msg = (
            "Azure batch transcription requires remotely accessible storage; "
            "STORAGE_SERVICE_NAME=local cannot provide Azure with an audio URL. "
            "Configure S3 or Azure Blob storage for recordings over two hours."
        )
        raise ValueError(msg)

    recording_id = uuid4()
    key = f"{key_prefix.rstrip('/')}/{recording_id}.mp3"
    recording = Recording(id=recording_id, user_id=uuid4(), s3_file_key=key)
    await storage_service.upload(key, audio_path)
    started_at = time.monotonic()
    timeout_seconds = max(MIN_BATCH_TRANSCRIPTION_TIMEOUT_SECONDS, duration * 2)

    try:
        job = await AzureBatchTranscriptionAdapter.start(recording)
        while time.monotonic() - started_at < timeout_seconds:
            await asyncio.sleep(BATCH_TRANSCRIPTION_POLL_SECONDS)
            job = await AzureBatchTranscriptionAdapter.check(job)
            if job.transcript is not None:
                entries = job.transcript or []
                return entries, time.monotonic() - started_at
        msg = f"Azure batch transcription did not complete within {timeout_seconds / 60:g} minutes"
        raise TimeoutError(msg)
    finally:
        try:
            await storage_service.delete(key)
        except Exception as error:  # noqa: BLE001 - cleanup must not mask the transcription result
            logger.warning("Could not delete temporary batch audio %s: %s", key, error)

