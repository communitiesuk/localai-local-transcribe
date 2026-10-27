"""Provenance metadata for silver transcript generation."""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Literal

from pydantic import BaseModel, Field

from evals.dataset_generation.silver_transcripts.src.config import DEFAULT_SEGMENT_DURATION_SECONDS
from evals.transcription.src.models import DialogueEntry, TranscriptionResult


class MeetingMetadata(BaseModel):
    """Source identity, generation status and meeting-level transcription statistics."""

    sample_id: str
    source_audio: str
    engine: str
    generated_at: str
    status: Literal["failed", "completed"] = "failed"
    segment_duration_seconds: float | None = Field(
        default=DEFAULT_SEGMENT_DURATION_SECONDS,
    )
    segment_count: int | None = None
    utterance_count: int | None = None
    scored_utterance_count: int | None = None
    mean_utterance_confidence: float | None = None
    std_utterance_confidence: float | None = None
    error: str | None = None

    @classmethod
    def from_transcription(
        cls,
        source: MeetingMetadata,
        result: TranscriptionResult,
    ) -> MeetingMetadata:
        """Build completed metadata from a successful transcription and its source identity."""
        utterances = result.dialogue_entries
        count, average, deviation = cls.confidence_statistics(utterances)
        return cls(
            sample_id=source.sample_id,
            source_audio=source.source_audio,
            segment_duration_seconds=source.segment_duration_seconds,
            engine=source.engine,
            generated_at=source.generated_at,
            status="completed",
            utterance_count=len(utterances),
            scored_utterance_count=count,
            mean_utterance_confidence=average,
            std_utterance_confidence=deviation,
        )

    @staticmethod
    def confidence_statistics(utterances: list[DialogueEntry]) -> tuple[int, float | None, float | None]:
        """
        Summarise engine confidence as a scored count, unweighted mean and population deviation.

        Utterances the engine did not score are excluded, so the aggregates are null when
        nothing was scored.
        """
        scores = [float(score) for entry in utterances if isinstance((score := entry.get("confidence")), int | float)]
        return len(scores), mean(scores) if scores else None, pstdev(scores) if scores else None


class SegmentMetadata(MeetingMetadata):
    """
    Provenance for a chunk, including its interval in the source meeting.
    """

    meeting_id: str
    source_start_seconds: float
    source_end_seconds: float

    @classmethod
    def from_utterances(
        cls,
        meeting: MeetingMetadata,
        *,
        sample_id: str,
        utterances: list[DialogueEntry],
        source_start_seconds: float,
        source_end_seconds: float,
    ) -> SegmentMetadata:
        """Build chunk statistics using the same aggregation as meeting metadata."""
        count, average, deviation = cls.confidence_statistics(utterances)
        return cls.model_validate(
            {
                **meeting.model_dump(exclude_unset=True, exclude={"segment_count"}),
                "sample_id": sample_id,
                "meeting_id": meeting.sample_id,
                "source_start_seconds": source_start_seconds,
                "source_end_seconds": source_end_seconds,
                "utterance_count": len(utterances),
                "scored_utterance_count": count,
                "mean_utterance_confidence": average,
                "std_utterance_confidence": deviation,
            }
        )
