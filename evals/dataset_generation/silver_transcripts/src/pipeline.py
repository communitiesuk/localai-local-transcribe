"""
Generate Azure draft transcripts and reviewable audio segments for one meeting at a time.
"""

from __future__ import annotations

import logging
import math
import re
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import ffmpeg
import httpx
import soundfile
from ffmpeg import Error as FFmpegError

from common.audio.ffmpeg import MP3_ENCODING_OPTIONS, convert_to_mp3
from common.database.postgres_models import DialogueEntry
from common.services.exceptions import TranscriptionFailedError
from common.services.transcription_services.azure import AzureSpeechAdapter
from evals.dataset_generation.silver_transcripts.src.config import DEFAULT_CUTOFF_SECONDS
from evals.dataset_generation.silver_transcripts.src.models import MeetingMetadata, SegmentMetadata
from evals.transcription.src.adapters.base import EvalsTranscriptionAdapter, ServiceTranscriptionAdapter

logger = logging.getLogger(__name__)
TIMESTAMP_TOLERANCE_SECONDS = 0.05
AUDIO_SUFFIXES = {".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac"}
MAX_SEGMENT_SPAN_FACTOR = 2
MAX_SAMPLE_NAME_LENGTH = 60


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
        cutoff_seconds: float = DEFAULT_CUTOFF_SECONDS,
    ) -> None:
        if not math.isfinite(cutoff_seconds) or cutoff_seconds <= 0:
            message = "cutoff_seconds must be finite and greater than zero"
            raise ValueError(message)
        self.cutoff_seconds = cutoff_seconds
        self.work_dir = work_dir.expanduser().resolve()
        self.adapter = adapter or ServiceTranscriptionAdapter(AzureSpeechAdapter)

    def generate_transcripts(self, input_dir: Path) -> list[MeetingMetadata]:
        """
        Generate draft transcripts, resuming any sample already recorded as completed.

        Args:
            input_dir: Directory containing source audio files, searched recursively.

        Returns:
            Meeting metadata, one entry per input audio file, including resumed drafts
            and newly processed successes or failures.

        Raises:
            NotADirectoryError: If input_dir does not exist or is not a directory.
            ValueError: If work_dir is inside input_dir, no supported audio files are found,
                existing draft metadata is invalid, or a completed draft was generated with a
                different cutoff_seconds.
            OSError: If input discovery or reading or writing draft files fails.
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
            draft_dir = self.work_dir / "drafts" / self._sample_id(relative_path, source.stem)
            metadata_path = draft_dir / "metadata.json"
            if metadata_path.exists():
                existing_metadata = MeetingMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
                if existing_metadata.status == "completed":
                    if existing_metadata.cutoff_seconds != self.cutoff_seconds:
                        message = "Existing draft uses a different cutoff_seconds; use a new work_dir or move it aside"
                        raise ValueError(message)
                    meeting_metadata.append(existing_metadata)
                    continue
            meeting_metadata.append(self._generate_transcript(source, draft_dir, relative_path))
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
        meeting_metadata = MeetingMetadata(
            sample_id=draft_dir.name,
            source_audio=relative_path,
            cutoff_seconds=self.cutoff_seconds,
            engine=self.adapter.name,
            generated_at=datetime.now(UTC).isoformat(),
            status="failed",
        )
        audio_path = draft_dir / "audio.mp3"
        try:
            # Publish only complete MP3s, using the correct suffix for ffmpeg's format detection.
            with tempfile.TemporaryDirectory(dir=draft_dir) as temporary_dir:
                converted = Path(temporary_dir) / "audio.mp3"
                convert_to_mp3(source, converted)
                converted.replace(audio_path)
            transcript_result = self.adapter.transcribe(str(audio_path))
            if transcript_result.debug_info.get("error") or not transcript_result.text.strip():
                message = str(transcript_result.debug_info.get("error") or "The engine returned an empty transcript")
                raise RuntimeError(message)
            transcript = transcript_result.text.strip() + "\n"
            (draft_dir / "draft.txt").write_text(transcript, encoding="utf-8")
            utterances = transcript_result.dialogue_entries
            completed_metadata = MeetingMetadata.from_transcription(
                source=meeting_metadata,
                result=transcript_result,
            )
            self._write_segments(audio_path, draft_dir, utterances, completed_metadata)
            meeting_metadata = completed_metadata
        except (OSError, RuntimeError, ValueError, FFmpegError, httpx.HTTPError, TranscriptionFailedError) as error:
            meeting_metadata.error = str(error)
            logger.error("Could not generate %s: %s", source, error)
        _save_metadata(metadata_path, meeting_metadata)
        return meeting_metadata

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
        for entry in sorted(utterances, key=lambda item: item["start_time"]):
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
        transcript.txt plus metadata.json under draft_dir/segments.

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
                segment_text = " ".join(entry["text"] for entry in segment_utterances).strip() + "\n"
                (segment_dir / "transcript.txt").write_text(segment_text, encoding="utf-8")
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
