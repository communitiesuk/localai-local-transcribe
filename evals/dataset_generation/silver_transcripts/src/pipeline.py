"""
Generate Azure draft transcripts and reviewable audio segments for one meeting at a time.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

import ffmpeg
import soundfile
from tenacity import RetryError

from common.audio.ffmpeg import MP3_ENCODING_OPTIONS, convert_to_mp3
from common.database.postgres_models import DialogueEntry, Recording
from common.services.storage_services import get_storage_service
from common.services.transcription_services.azure import AzureSpeechAdapter
from common.services.transcription_services.azure_async import AzureBatchTranscriptionAdapter
from common.settings import get_settings
from evals.dataset_generation.silver_transcripts.src.config import DEFAULT_CUTOFF_SECONDS
from evals.dataset_generation.silver_transcripts.src.models import MeetingMetadata, SegmentMetadata
from evals.transcription.src.adapters.base import EvalsTranscriptionAdapter, ServiceTranscriptionAdapter
from evals.transcription.src.models import TranscriptionResult

logger = logging.getLogger(__name__)
TIMESTAMP_TOLERANCE_SECONDS = 0.05
AUDIO_SUFFIXES = {".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac"}
MAX_SEGMENT_SPAN_FACTOR = 2
MAX_SAMPLE_NAME_LENGTH = 60
MAX_SYNCHRONOUS_TRANSCRIPTION_SECONDS = AzureSpeechAdapter.max_audio_length
MAX_BATCH_TRANSCRIPTION_SECONDS = AzureBatchTranscriptionAdapter.max_audio_length
BATCH_TRANSCRIPTION_POLL_SECONDS = 5
MIN_BATCH_TRANSCRIPTION_TIMEOUT_SECONDS = 1800


class CutoffMismatchError(ValueError):
    """
    An existing draft was generated with a different cutoff_seconds.

    Raised rather than recorded per sample: the cutoff comes from the config, so every existing
    draft mismatches and one clear message is more useful than a failure against each sample.
    """


def _save_metadata(path: Path, metadata: MeetingMetadata) -> None:
    path.write_text(metadata.model_dump_json(indent=2, exclude_unset=True) + "\n", encoding="utf-8")


def _error_message(error: BaseException) -> str:
    """
    Describe a failure for the error field, reporting the cause behind an exhausted retry.

    Tenacity raises RetryError once its attempts are spent, whose repr names a Future at a memory
    address rather than what actually went wrong.
    """
    if isinstance(error, RetryError) and error.last_attempt.failed:
        attempts = error.last_attempt.attempt_number
        return f"{error.last_attempt.exception()} (after {attempts} attempts)"
    return str(error)


class SilverTranscriptPipeline:
    """
    Generate draft transcripts and audio segments for human annotation.
    """

    def __init__(
        self,
        work_dir: Path,
        adapter: EvalsTranscriptionAdapter | None = None,
        *,
        cutoff_seconds: float = DEFAULT_CUTOFF_SECONDS,
    ) -> None:
        if not math.isfinite(cutoff_seconds) or cutoff_seconds <= 0:
            message = "cutoff_seconds must be finite and greater than zero"
            raise ValueError(message)
        self.cutoff_seconds = cutoff_seconds
        self.work_dir = work_dir.expanduser().resolve()
        self.adapter = adapter or ServiceTranscriptionAdapter(AzureSpeechAdapter)
        self._uses_default_adapter = getattr(self.adapter, "_adapter", None) is AzureSpeechAdapter

    def generate_transcripts(self, input_dir: Path) -> list[MeetingMetadata]:
        """
        Generate draft transcripts, resuming any sample already recorded as completed.

        Args:
            input_dir: Directory containing source audio files, searched recursively.

        Returns:
            Meeting metadata, one entry per input audio file, including resumed drafts
            and newly processed successes or failures.

        A sample that cannot be processed is recorded as failed and skipped, so one bad input
        never abandons the rest of the batch.

        Raises:
            NotADirectoryError: If input_dir does not exist or is not a directory.
            ValueError: If work_dir is inside input_dir or no supported audio files are found.
            CutoffMismatchError: If a completed draft was generated with a different cutoff_seconds.
            OSError: If input discovery fails.
        """
        input_dir = input_dir.expanduser().resolve()
        if not input_dir.is_dir():
            raise NotADirectoryError(input_dir)
        if self.work_dir.is_relative_to(input_dir):
            message = "work_dir must be outside input_dir so generated audio is not discovered as input"
            raise ValueError(message)
        audio_sources = sorted(
            path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
        )
        if not audio_sources:
            message = f"No supported audio files found in {input_dir}"
            raise ValueError(message)
        meeting_metadata = []
        for source in audio_sources:
            relative_path = source.relative_to(input_dir).as_posix()
            sample_id = self._sample_id(relative_path, source.stem)
            try:
                meeting_metadata.append(self._process_sample(source, relative_path, sample_id))
            except CutoffMismatchError:
                raise
            except Exception as error:  # noqa: BLE001 - one bad sample must not stop the folder
                logger.error("Could not process %s: %s", source, _error_message(error))
                meeting_metadata.append(self._failure_metadata(relative_path, sample_id, error=error))
        return meeting_metadata

    def _process_sample(self, source: Path, relative_path: str, sample_id: str) -> MeetingMetadata:
        """
        Resume a completed draft for one sample, or generate it.
        """
        draft_dir = self.work_dir / "drafts" / sample_id
        metadata_path = draft_dir / "metadata.json"
        if metadata_path.exists():
            existing_metadata = MeetingMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
            if existing_metadata.status == "completed":
                if existing_metadata.cutoff_seconds != self.cutoff_seconds:
                    message = "Existing draft uses a different cutoff_seconds; use a new work_dir or move it aside"
                    raise CutoffMismatchError(message)
                return existing_metadata
        return self._generate_transcript(source, draft_dir, relative_path)

    def _failure_metadata(
        self, relative_path: str, sample_id: str, *, error: BaseException | None = None
    ) -> MeetingMetadata:
        """
        Build the failed record a sample starts from, carrying an error once one is known.

        An unknown error is left unset rather than null, so it stays out of the serialised draft.
        """
        meeting_metadata = MeetingMetadata(
            sample_id=sample_id,
            source_audio=relative_path,
            cutoff_seconds=self.cutoff_seconds,
            engine=self.adapter.name,
            generated_at=datetime.now(UTC).isoformat(),
            status="failed",
        )
        if error is not None:
            meeting_metadata.error = _error_message(error)
        return meeting_metadata

    @staticmethod
    def _sample_id(relative_path: str, stem: str) -> str:
        """
        Build a stable draft identity from the path a sample was discovered at.
        """
        identity = uuid5(NAMESPACE_URL, relative_path).hex[:16]
        name = re.sub(r"[^a-zA-Z0-9_-]", "_", stem)[:MAX_SAMPLE_NAME_LENGTH] or "audio"
        return f"{name}-{identity}"

    def _generate_transcript(self, source: Path, draft_dir: Path, relative_path: str) -> MeetingMetadata:
        """
        Prepare and transcribe one sample, recording service or conversion failures.
        Returns meeting metadata.
        """
        metadata_path = draft_dir / "metadata.json"
        draft_dir.mkdir(parents=True, exist_ok=True)
        meeting_metadata = self._failure_metadata(relative_path, draft_dir.name)
        audio_path = draft_dir / "audio.mp3"
        try:
            # Publish only complete MP3s, using the correct suffix for ffmpeg's format detection.
            with tempfile.TemporaryDirectory(dir=draft_dir) as temporary_dir:
                converted = Path(temporary_dir) / "audio.mp3"
                convert_to_mp3(source, converted)
                converted.replace(audio_path)
            audio_info = soundfile.info(audio_path)
            duration = audio_info.frames / audio_info.samplerate
            use_batch_adapter = self._uses_default_adapter and duration > MAX_SYNCHRONOUS_TRANSCRIPTION_SECONDS
            if use_batch_adapter:
                meeting_metadata.engine = AzureBatchTranscriptionAdapter.name
            transcript_result = self._transcribe(audio_path, duration, use_batch_adapter)
            if transcript_result.debug_info.get("error") or not transcript_result.text.strip():
                message = str(transcript_result.debug_info.get("error") or "The engine returned an empty transcript")
                raise RuntimeError(message)
            utterances = self.sort_utterances(transcript_result.dialogue_entries)
            transcript = self._format_diarized_transcript(utterances)
            (draft_dir / "draft.txt").write_text(transcript, encoding="utf-8")
            completed_metadata = MeetingMetadata.from_transcription(
                source=meeting_metadata,
                result=transcript_result,
            )
            self._write_segments(audio_path, draft_dir, utterances, completed_metadata)
            meeting_metadata = completed_metadata
        except Exception as error:  # noqa: BLE001 - record per-sample conversion/transcription failures
            meeting_metadata.error = _error_message(error)
            logger.error("Could not generate %s: %s", source, meeting_metadata.error)
        _save_metadata(metadata_path, meeting_metadata)
        return meeting_metadata

    def _transcribe(self, audio_path: Path, duration: float, use_batch_adapter: bool) -> TranscriptionResult:
        """Use Azure's existing async batch adapter for recordings over its two-hour limit."""
        if not use_batch_adapter:
            return self.adapter.transcribe(str(audio_path))
        if duration > MAX_BATCH_TRANSCRIPTION_SECONDS:
            message = f"Recording is {duration / 3600:.1f} hours long; Azure batch transcription supports up to 4 hours"
            raise ValueError(message)
        return asyncio.run(self._transcribe_with_azure_batch(audio_path, duration))

    async def _transcribe_with_azure_batch(self, audio_path: Path, duration: float) -> TranscriptionResult:
        """Upload a local file and run the existing stored-recording batch adapter flow."""
        storage_service = get_storage_service(get_settings().STORAGE_SERVICE_NAME)
        if storage_service.name == "local":
            message = (
                "Azure batch transcription requires remotely accessible storage; "
                "STORAGE_SERVICE_NAME=local cannot provide Azure with an audio URL. "
                "Configure S3 or Azure Blob storage for recordings over two hours."
            )
            raise ValueError(message)
        recording_id = uuid4()
        key = f"silver-transcripts/{recording_id}.mp3"
        recording = Recording(id=recording_id, user_id=uuid4(), s3_file_key=key)
        await storage_service.upload(key, audio_path)
        started_at = time.monotonic()
        timeout_seconds = max(MIN_BATCH_TRANSCRIPTION_TIMEOUT_SECONDS, duration * 2)
        job_submitted = False
        job_completed = False
        try:
            job = await AzureBatchTranscriptionAdapter.start(recording)
            job_submitted = True
            while time.monotonic() - started_at < timeout_seconds:
                await asyncio.sleep(BATCH_TRANSCRIPTION_POLL_SECONDS)
                job = await AzureBatchTranscriptionAdapter.check(job)
                if job.job_status == "Succeeded":
                    job_completed = True
                    entries = job.transcript or []
                    return TranscriptionResult(
                        text=" ".join(entry["text"] for entry in entries).strip(),
                        duration_sec=time.monotonic() - started_at,
                        debug_info={},
                        dialogue_entries=entries,
                    )
            message = f"Azure batch transcription did not complete within {timeout_seconds / 60:g} minutes"
            raise TimeoutError(message)
        finally:
            if job_submitted and not job_completed:
                logger.warning("Retaining %s because the Azure batch job did not complete", key)
            else:
                try:
                    await storage_service.delete(key)
                except Exception as error:  # noqa: BLE001 - cleanup must not mask the transcription result
                    logger.warning("Could not delete temporary batch audio %s: %s", key, error)

    @staticmethod
    def _format_diarized_transcript(utterances: list[DialogueEntry]) -> str:
        """Format every utterance with its speaker label on a separate line."""
        return "\n".join(f"Speaker {entry['speaker']}: {entry['text']}" for entry in utterances).strip() + "\n"

    @staticmethod
    def group_utterances(
        utterances: list[DialogueEntry], cutoff_seconds: float = DEFAULT_CUTOFF_SECONDS
    ) -> list[list[DialogueEntry]]:
        """
        Pack whole utterances into windows targeting cutoff_seconds, keeping overlapping speech together.
        """
        max_span_seconds = cutoff_seconds * MAX_SEGMENT_SPAN_FACTOR
        segment_groups: list[list[DialogueEntry]] = []
        active_window_end_sec = 0.0
        for entry in SilverTranscriptPipeline.sort_utterances(utterances):
            utterance_start, utterance_end = entry["start_time"], entry["end_time"]
            if not (
                math.isfinite(utterance_start) and math.isfinite(utterance_end) and 0 <= utterance_start < utterance_end
            ):
                message = "Utterances must have non-negative start times and end after their start"
                raise ValueError(message)
            if not segment_groups:
                start_new_segment = True
            else:
                span_seconds = utterance_end - segment_groups[-1][0]["start_time"]
                start_new_segment = (utterance_start >= active_window_end_sec and span_seconds > cutoff_seconds) or (
                    span_seconds > max_span_seconds
                )
            if start_new_segment:
                segment_groups.append([])
                active_window_end_sec = 0.0
            segment_groups[-1].append(entry)
            active_window_end_sec = max(active_window_end_sec, utterance_end)
        if not segment_groups:
            message = "Utterance timestamps are required to generate audio segments"
            raise ValueError(message)
        return segment_groups

    @staticmethod
    def sort_utterances(utterances: list[DialogueEntry]) -> list[DialogueEntry]:
        """Return utterances in source-time order, preserving original order for ties."""
        return sorted(utterances, key=lambda item: item["start_time"])

    @staticmethod
    def cut_audio(source: Path, destination: Path, start: float, end: float) -> None:
        """
        Decode and re-encode the selected interval.
        """
        with tempfile.TemporaryDirectory(dir=destination.parent) as temporary_dir:
            converted = Path(temporary_dir) / "audio.mp3"
            stream = ffmpeg.input(str(source)).audio.filter("atrim", start=start, end=end)
            stream = stream.filter("asetpts", "PTS-STARTPTS")
            ffmpeg.output(stream, str(converted), **MP3_ENCODING_OPTIONS).run(overwrite_output=True, quiet=True)
            converted.replace(destination)

    def _write_segments(
        self, audio_path: Path, draft_dir: Path, utterances: list[DialogueEntry], meeting_metadata: MeetingMetadata
    ) -> None:
        """
        Split utterances into review segments, cut matching audio clips, and write per-segment
        audio.txt plus metadata.json under draft_dir/segments.

        Segments are first staged in a temporary directory and then atomically moved into place.
        Raises ValueError if utterance timestamps are invalid or exceed the source audio duration.
        """
        segment_utterance_groups = self.group_utterances(utterances, self.cutoff_seconds)
        audio_info = soundfile.info(audio_path)
        duration = audio_info.frames / audio_info.samplerate
        if any(entry["end_time"] > duration + TIMESTAMP_TOLERANCE_SECONDS for entry in utterances):
            message = "Utterance timestamps exceed the audio duration"
            raise ValueError(message)
        meeting_metadata.segment_count = len(segment_utterance_groups)
        with tempfile.TemporaryDirectory(dir=draft_dir) as temporary_dir:
            staging = Path(temporary_dir) / "segments"
            staging.mkdir()
            for index, segment_utterances in enumerate(segment_utterance_groups):
                segment_dir = staging / f"segment_{index:04d}"
                segment_dir.mkdir()
                segment_start = segment_utterances[0]["start_time"]
                segment_end = max(entry["end_time"] for entry in segment_utterances)
                self.cut_audio(audio_path, segment_dir / "audio.mp3", segment_start, segment_end)
                segment_text = self._format_diarized_transcript(segment_utterances)
                (segment_dir / "audio.txt").write_text(segment_text, encoding="utf-8")
                _save_metadata(
                    segment_dir / "metadata.json",
                    SegmentMetadata.from_utterances(
                        meeting_metadata,
                        sample_id=f"{draft_dir.name}_{segment_dir.name}",
                        utterances=segment_utterances,
                        source_start_seconds=segment_start,
                        source_end_seconds=segment_end,
                    ),
                )
            destination = draft_dir / "segments"
            if destination.exists():
                shutil.rmtree(destination)
            staging.replace(destination)
