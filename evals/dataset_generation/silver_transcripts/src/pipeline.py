"""
Generate Azure draft transcripts and reviewable audio segments for one meeting at a time.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import soundfile

from common.audio.ffmpeg import convert_to_mp3
from common.constants import SUPPORTED_AUDIO_SUFFIXES
from common.services.transcription_services.azure import AzureSpeechAdapter
from common.services.transcription_services.azure_async import AzureBatchTranscriptionAdapter
from evals.dataset_generation.silver_transcripts.src.config import DEFAULT_SEGMENT_DURATION_SECONDS
from evals.dataset_generation.silver_transcripts.src.core.batch_transcription import transcribe_with_azure_batch
from evals.dataset_generation.silver_transcripts.src.core.ids import build_sample_id
from evals.dataset_generation.silver_transcripts.src.core.segments import (
    cut_audio,
    format_diarized_transcript,
    group_utterances,
    write_segments,
)
from evals.dataset_generation.silver_transcripts.src.models import MeetingMetadata
from evals.transcription.src.adapters.base import EvalsTranscriptionAdapter, ServiceTranscriptionAdapter
from evals.transcription.src.models import DialogueEntry, TranscriptionResult

logger = logging.getLogger(__name__)
MAX_SYNCHRONOUS_TRANSCRIPTION_SECONDS = AzureSpeechAdapter.max_audio_length
MAX_BATCH_TRANSCRIPTION_SECONDS = AzureBatchTranscriptionAdapter.max_audio_length


class SegmentDurationMismatchError(ValueError):
    """
    An existing draft was generated with a different segment_duration_seconds.
    """


def _save_metadata(path: Path, metadata: MeetingMetadata) -> None:
    path.write_text(metadata.model_dump_json(indent=2, exclude_unset=True) + "\n", encoding="utf-8")


class SilverTranscriptPipeline:
    """
    Generate draft transcripts and audio segments for human annotation.
    """

    def __init__(
        self,
        work_dir: Path,
        adapter: EvalsTranscriptionAdapter | None = None,
        *,
        segment_duration_seconds: float | None = DEFAULT_SEGMENT_DURATION_SECONDS,
    ) -> None:
        self.segment_duration_seconds = segment_duration_seconds
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
            OSError: If input discovery fails.
        """
        input_dir = input_dir.expanduser().resolve()
        if not input_dir.is_dir():
            raise NotADirectoryError(input_dir)
        if self.work_dir.is_relative_to(input_dir):
            message = "work_dir must be outside input_dir so generated audio is not discovered as input"
            raise ValueError(message)
        audio_sources = sorted(
            path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_SUFFIXES
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
            except SegmentDurationMismatchError:
                raise
            except Exception as error:  # noqa: BLE001 - one bad sample must not stop the folder
                logger.error("Could not process %s: %s", source, error)
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
                if existing_metadata.segment_duration_seconds != self.segment_duration_seconds:
                    message = (
                        "Existing draft uses a different segment_duration_seconds; "
                        "use a new work_dir or move it aside"
                    )
                    raise SegmentDurationMismatchError(message)
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
            segment_duration_seconds=self.segment_duration_seconds,
            engine=self.adapter.name,
            generated_at=datetime.now(UTC).isoformat(),
            status="failed",
        )
        if error is not None:
            meeting_metadata.error = str(error)
        return meeting_metadata

    @staticmethod
    def _sample_id(relative_path: str, stem: str) -> str:
        return build_sample_id(relative_path, stem)

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
            segment_utterance_groups = self.group_utterances(transcript_result.dialogue_entries)
            transcript = self._format_diarized_transcript(segment_utterance_groups[0])
            (draft_dir / "draft.txt").write_text(transcript, encoding="utf-8")
            completed_metadata = MeetingMetadata(
                sample_id=meeting_metadata.sample_id,
                source_audio=meeting_metadata.source_audio,
                segment_duration_seconds=meeting_metadata.segment_duration_seconds,
                engine=meeting_metadata.engine,
                generated_at=meeting_metadata.generated_at,
                status="completed",
            )
            self._write_segments(audio_path, draft_dir, segment_utterance_groups, completed_metadata)
            meeting_metadata = completed_metadata
        except Exception as error:  # noqa: BLE001 - record per-sample conversion/transcription failures
            meeting_metadata.error = str(error)
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
        return asyncio.run(transcribe_with_azure_batch(audio_path, duration))

    async def _transcribe_with_azure_batch(self, audio_path: Path, duration: float) -> TranscriptionResult:
        """Compatibility wrapper around the extracted batch helper."""
        return await transcribe_with_azure_batch(audio_path, duration)

    @staticmethod
    def _format_diarized_transcript(utterances: list[DialogueEntry]) -> str:
        return format_diarized_transcript(utterances)

    @staticmethod
    def group_utterances(utterances: list[DialogueEntry]) -> list[list[DialogueEntry]]:
        return group_utterances(utterances)

    @staticmethod
    def cut_audio(source: Path, destination: Path, start: float, end: float) -> None:
        cut_audio(source, destination, start, end)

    def _write_segments(
        self,
        audio_path: Path,
        draft_dir: Path,
        segment_utterance_groups: list[list[DialogueEntry]],
        meeting_metadata: MeetingMetadata,
    ) -> None:
        write_segments(audio_path, draft_dir, segment_utterance_groups, meeting_metadata, self.cut_audio)
