"""Provenance metadata for silver transcript generation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from evals.dataset_generation.silver_transcripts.src.config import DEFAULT_SEGMENT_DURATION_SECONDS


class MeetingMetadata(BaseModel):
    """Source identity and generation status for one meeting."""

    sample_id: str
    source_audio: str
    engine: str
    generated_at: str
    status: Literal["failed", "completed"] = "failed"
    segment_duration_seconds: float | None = Field(
        default=DEFAULT_SEGMENT_DURATION_SECONDS,
    )
    segment_count: int | None = None
    error: str | None = None


class SegmentMetadata(MeetingMetadata):
    """
    Provenance for a chunk, including its interval in the source meeting.
    """

    meeting_id: str
    source_start_seconds: float
    source_end_seconds: float
