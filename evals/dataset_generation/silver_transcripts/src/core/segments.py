"""Helpers for transcript text and segment file writing."""

from __future__ import annotations

import math
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

import ffmpeg
import soundfile

from evals.dataset_generation.silver_transcripts.src.models import MeetingMetadata, SegmentMetadata
from evals.transcription.src.models import DialogueEntry

TIMESTAMP_TOLERANCE_SECONDS = 0.05
MP3_ENCODING_OPTIONS = {
    "acodec": "libmp3lame",
    "audio_bitrate": "192k",
    "ac": 1,
}


def format_diarized_transcript(utterances: list[DialogueEntry]) -> str:
    """Format every utterance with its speaker label on a separate line."""
    return "\n".join(f"Speaker {entry['speaker']}: {entry['text']}" for entry in utterances).strip() + "\n"


def group_utterances(utterances: list[DialogueEntry]) -> list[list[DialogueEntry]]:
    """Validate and keep the whole recording in a single segment."""
    ordered = sorted(utterances, key=lambda item: item["start_time"])
    for entry in ordered:
        start_time, end_time = entry["start_time"], entry["end_time"]
        if not (math.isfinite(start_time) and math.isfinite(end_time) and 0 <= start_time < end_time):
            msg = "Utterances must have non-negative start times and end after their start"
            raise ValueError(msg)
    if not ordered:
        msg = "Utterance timestamps are required to generate audio segments"
        raise ValueError(msg)
    return [ordered]


def cut_audio(source: Path, destination: Path, start: float, end: float) -> None:
    """Decode and re-encode the selected interval."""
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary_dir:
        converted = Path(temporary_dir) / "audio.mp3"
        stream = ffmpeg.input(str(source)).audio.filter("atrim", start=start, end=end)
        stream = stream.filter("asetpts", "PTS-STARTPTS")
        ffmpeg.output(stream, str(converted), **MP3_ENCODING_OPTIONS).run(overwrite_output=True, quiet=True)
        converted.replace(destination)


def write_segments(
    audio_path: Path,
    draft_dir: Path,
    segment_utterance_groups: list[list[DialogueEntry]],
    meeting_metadata: MeetingMetadata,
    cut_audio_fn: Callable[[Path, Path, float, float], None] = cut_audio,
) -> None:
    """Write segment audio/text/metadata files for the generated draft."""
    audio_info = soundfile.info(audio_path)
    duration = audio_info.frames / audio_info.samplerate
    if any(
        entry["end_time"] > duration + TIMESTAMP_TOLERANCE_SECONDS
        for segment_utterances in segment_utterance_groups
        for entry in segment_utterances
    ):
        msg = "Utterance timestamps exceed the audio duration"
        raise ValueError(msg)

    segments_dir = draft_dir / "segments"
    if segments_dir.exists():
        shutil.rmtree(segments_dir)
    segments_dir.mkdir(parents=True, exist_ok=True)

    meeting_metadata.segment_count = len(segment_utterance_groups)
    for index, segment_utterances in enumerate(segment_utterance_groups):
        segment_dir = segments_dir / f"segment_{index:04d}"
        segment_dir.mkdir()
        segment_start = segment_utterances[0]["start_time"]
        segment_end = max(entry["end_time"] for entry in segment_utterances)
        cut_audio_fn(audio_path, segment_dir / "audio.mp3", segment_start, segment_end)
        (segment_dir / "audio.txt").write_text(format_diarized_transcript(segment_utterances), encoding="utf-8")
        metadata = SegmentMetadata.model_validate(
            {
                **meeting_metadata.model_dump(exclude_unset=True, exclude={"segment_count"}),
                "sample_id": f"{draft_dir.name}_{segment_dir.name}",
                "meeting_id": meeting_metadata.sample_id,
                "source_start_seconds": segment_start,
                "source_end_seconds": segment_end,
            }
        )
        (segment_dir / "metadata.json").write_text(metadata.model_dump_json(indent=2, exclude_unset=True) + "\n")
