from dataclasses import dataclass
from typing import Literal

from common.database.postgres_models import AnalyticsEventType, RecordingSource

Source = Literal["plausible", "postgres"]

# Plausible event names, as set by frontend/lib/analytics.ts.
LIVE_RECORDING_STARTED = "live_recording_started"
AUDIO_UPLOAD_COMPLETE_FROM_LIVE_RECORDING = "audio_upload_complete_from_live_recording"
AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD = "audio_upload_complete_from_direct_upload"
TRANSCRIPT_REQUESTED_FOR_LIVE_RECORDING = "transcript_requested_for_live_recording"
SUMMARY_REQUESTED = "summary_requested"

# analytics_event.event_type values are stored by enum name.
TRANSCRIPTION_RECEIVED = AnalyticsEventType.TRANSCRIPTION_RECEIVED.name
SUMMARY_RECEIVED = AnalyticsEventType.SUMMARY_RECEIVED.name


@dataclass(frozen=True)
class Count:
    """A single event count. `event` is a Plausible event name or an analytics_event type, per `source`."""

    source: Source
    event: str
    # Postgres only: restrict to events whose metadata records this recording source.
    recording_source: str | None = None

    @property
    def label(self) -> str:
        """Name shown next to this count in the report."""
        return f"{self.event}, {self.recording_source}" if self.recording_source else self.event


@dataclass(frozen=True)
class RatioMeasure:
    name: str
    numerator: Count
    denominator: Count


@dataclass(frozen=True)
class MonthlyMeasure:
    """Count of events per calendar month. `events` are summed."""

    name: str
    source: Source
    events: tuple[str, ...]


@dataclass(frozen=True)
class MonthlyCaseloadMeasure:
    """Count of events per organisation and calendar month, against estimated caseload. `events` are summed."""

    name: str
    source: Source
    events: tuple[str, ...]


Measure = RatioMeasure | MonthlyMeasure | MonthlyCaseloadMeasure

LIVE_RECORDINGS_STARTED = Count("plausible", LIVE_RECORDING_STARTED)
TRANSCRIPTS_RECEIVED = Count("postgres", TRANSCRIPTION_RECEIVED)
SUMMARIES_RECEIVED = Count("postgres", SUMMARY_RECEIVED)

MEASURES: list[Measure] = [
    RatioMeasure(
        "Audio uploads per live recording start",
        Count("plausible", AUDIO_UPLOAD_COMPLETE_FROM_LIVE_RECORDING),
        LIVE_RECORDINGS_STARTED,
    ),
    RatioMeasure(
        "Transcription requests per live recording start",
        Count("plausible", TRANSCRIPT_REQUESTED_FOR_LIVE_RECORDING),
        LIVE_RECORDINGS_STARTED,
    ),
    RatioMeasure(
        "Transcription receipts per live recording start",
        Count("postgres", TRANSCRIPTION_RECEIVED, recording_source=RecordingSource.LIVE_RECORDING.value),
        LIVE_RECORDINGS_STARTED,
    ),
    RatioMeasure(
        "Summary requests per transcript received",
        Count("plausible", SUMMARY_REQUESTED),
        TRANSCRIPTS_RECEIVED,
    ),
    RatioMeasure(
        "Summary receipts per transcript received",
        SUMMARIES_RECEIVED,
        TRANSCRIPTS_RECEIVED,
    ),
    MonthlyCaseloadMeasure(
        "Audio uploads versus estimated organisation caseload",
        "plausible",
        (AUDIO_UPLOAD_COMPLETE_FROM_LIVE_RECORDING, AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD),
    ),
    MonthlyCaseloadMeasure("Summaries versus estimated caseload", "postgres", (SUMMARY_RECEIVED,)),
    MonthlyMeasure("Overall summaries created per month", "postgres", (SUMMARY_RECEIVED,)),
]
