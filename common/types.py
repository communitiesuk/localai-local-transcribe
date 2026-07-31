import re
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from common.constants import MAX_AGENDA_LENGTH
from common.database.postgres_models import (
    JobStatus,
)

DOMAIN_REGEX = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z-]{0,61}[a-z]$",
    re.IGNORECASE,
)


def validate_fqdn_list(domains: list[str]) -> list[str]:
    for domain in domains:
        if not DOMAIN_REGEX.match(domain):
            message = f"Domain '{domain}' is not a valid fully qualified domain name (FQDN)"
            raise ValueError(message)
    return domains


class LabelledTranscriptionMetadata(BaseModel):
    """Pydantic model for labelled transcription metadata."""

    id: uuid.UUID
    created_datetime: datetime
    title: str | None = None
    text: str
    status: JobStatus
    date_of_recording: datetime | None = None
    client_date_of_birth: datetime | None = None
    client_name: str | None = None
    case_id: str | None = None


class LabelledTranscriptionsResponse(BaseModel):
    """Response for labelled transcriptions."""

    items: list[LabelledTranscriptionMetadata]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class UnlabelledTranscriptionMetadata(BaseModel):
    """Pydantic model for unlabelled transcription metadata."""

    id: uuid.UUID
    date_of_recording: datetime | None = None
    title: str | None = None
    text: str
    status: JobStatus


class UnlabelledTranscriptionsResponse(BaseModel):
    """Response for unlabelled transcriptions."""

    items: list[UnlabelledTranscriptionMetadata]
    total_count: int


class TranscriptionCreateRequest(BaseModel):
    recording_id: uuid.UUID
    template_name: str
    template_id: uuid.UUID | None = None
    agenda: str | None = Field(default=None, max_length=MAX_AGENDA_LENGTH)
    title: str | None = None


class RecordingCreateRequest(BaseModel):
    file_extension: str


class RecordingCreateResponse(BaseModel):
    id: uuid.UUID
    upload_url: str


class TranscriptionCreateResponse(BaseModel):
    id: uuid.UUID


class TranscriptionConfirmResponse(BaseModel):
    id: uuid.UUID


class UpdateTranscriptionTitleRequest(BaseModel):
    title: str | None = None
