import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum, auto
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from common.database.postgres_models import (
    ContentSource,
    DialogueEntry,
    JobStatus,
    TemplateType,
    UserRole,
)


class TranscriptionMetadata(BaseModel):
    """Pydantic model for transcription metadata."""

    id: uuid.UUID
    created_datetime: datetime
    title: str | None = None
    text: str
    status: JobStatus


class PaginatedTranscriptionsResponse(BaseModel):
    """Paginated response for transcriptions."""

    items: list[TranscriptionMetadata]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class TranscriptionCreateRequest(BaseModel):
    recording_id: uuid.UUID
    template_name: str
    template_id: uuid.UUID | None = None
    agenda: str | None = None
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


class RenameSpeakerRequest(BaseModel):
    original_speaker: str
    new_speaker: str


class UpdateDialogueEntrySpeakerRequest(BaseModel):
    new_speaker: str
    expected_speaker: str | None = None
    expected_start_time: float | None = None
    expected_end_time: float | None = None


class UpdateDialogueEntryTextRequest(BaseModel):
    new_text: str
    expected_text: str | None = None
    expected_speaker: str | None = None
    expected_start_time: float | None = None
    expected_end_time: float | None = None


class ChatCreateRequest(BaseModel):
    user_content: str


class ChatGetResponse(BaseModel):
    id: uuid.UUID
    created_datetime: datetime
    updated_datetime: datetime
    user_content: str
    assistant_content: str | None
    status: JobStatus


class ChatGetAllResponse(BaseModel):
    chat: list[ChatGetResponse]


class ChatCreateResponse(BaseModel):
    id: uuid.UUID


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    organisation_id: uuid.UUID


class UserUpdateRoles(BaseModel):
    roles: list[UserRole]


class GetUserResponse(BaseModel):
    id: uuid.UUID
    created_datetime: datetime
    updated_datetime: datetime
    accepted_tou: bool
    last_login: datetime
    is_active: bool
    name: str | None
    email: str
    data_retention_days: int
    roles: list[UserRole]
    organisation_id: uuid.UUID | None


class PaginatedUsersResponse(BaseModel):
    items: list[GetUserResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


type DataRetentionOptions = Literal[1, 7, 30, 90]


class DataRetentionUpdateResponse(BaseModel):
    data_retention_days: DataRetentionOptions


class TranscriptionGetResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    dialogue_entries: list[DialogueEntry] | None
    status: JobStatus
    created_datetime: datetime


class SingleRecording(BaseModel):
    id: uuid.UUID
    url: str
    extension: str


class MinuteListItem(BaseModel):
    id: uuid.UUID
    created_datetime: datetime
    updated_datetime: datetime
    transcription_id: uuid.UUID
    template_name: str
    agenda: str | None


class MinutesCreateRequest(BaseModel):
    template_name: str = Field(description="Name of the template to use for the minutes")
    template_id: uuid.UUID | None = Field(description="Optional id of user template")
    agenda: str | None = Field(description="The agenda for the meeting", default=None)


class AiEdit(BaseModel):
    instruction: str
    source_id: uuid.UUID


class MinuteVersionCreateRequest(BaseModel):
    ai_edit_instructions: AiEdit | None = Field(
        default=None,
        description="If the content source is an AI edit, store the instruction and source version id here",
    )
    content_source: ContentSource
    html_content: str = Field(default="")


class MinutesPatchRequest(BaseModel):
    html_content: str | None = None


class GuardrailResultResponse(BaseModel):
    id: uuid.UUID
    passed: bool
    score: float | None
    reasoning: str | None
    error: str | None


class LLMHallucination(BaseModel):
    hallucination_text: str = Field(description="The uncited claim flagged as a potential hallucination")
    hallucination_reason: str | None = Field(description="Reason the claim was flagged", default=None)


class GuardrailScore(BaseModel):
    score: float = Field(description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Reasoning for the score")


class MinuteVersionResponse(BaseModel):
    id: uuid.UUID
    minute_id: uuid.UUID
    status: JobStatus
    created_datetime: datetime
    html_content: str
    error: str | None
    ai_edit_instructions: str | None
    content_source: ContentSource
    too_short: bool = False
    guardrail_results: list[GuardrailResultResponse] = []


class SpeakerPrediction(BaseModel):
    original_speaker: str
    predicted_name: str
    confidence: float


class SpeakerPredictionOutput(BaseModel):
    predictions: list[SpeakerPrediction]


class MinutesResponse(BaseModel):
    minutes: str


class MeetingCheck(BaseModel):
    is_long_meeting: bool


class TaskType(IntEnum):
    # messages have a natural ordering in which we want them to happen
    TRANSCRIPTION = 1
    MINUTE = 2
    EDIT = 3
    INTERACTIVE = 4


class EditMessageData(BaseModel):
    source_id: uuid.UUID = Field(description="ID of the source message")


class TranscriptionJobMessageData(BaseModel):
    transcription_service: str = Field(description="Name of the transcription service")
    job_name: str = Field(
        description="job name to identify asynchronous jobs. Not used in case of synchronous jobs",
        default="synchronous",
    )
    transcript: list[DialogueEntry] | None = Field(description="Transcript of the transcription", default=None)


class WorkerMessage(BaseModel):
    id: uuid.UUID
    type: TaskType
    data: EditMessageData | TranscriptionJobMessageData | None = Field(default=None)


@dataclass
class MinuteAndHallucinations:
    text: str
    total_claims: int
    hallucinations: list[LLMHallucination]


class MeetingType(StrEnum):
    too_short = auto()
    short = auto()
    standard = auto()


class AgendaUsage(StrEnum):
    NOT_USED = auto()
    OPTIONAL = auto()
    REQUIRED = auto()


class TemplateMetadata(BaseModel):
    name: str
    description: str
    category: str
    agenda_usage: AgendaUsage


class CreateQuestion(BaseModel):
    position: int
    title: str
    description: str


class Question(CreateQuestion):
    id: uuid.UUID


class PatchUserTemplateRequest(BaseModel):
    name: str | None = None
    content: str | None = None
    description: str | None = None
    questions: list[CreateQuestion | Question] | None = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    updated_datetime: datetime
    name: str
    content: str
    description: str
    type: TemplateType
    questions: list[Question] | None


class CreateUserTemplateRequest(BaseModel):
    name: str
    content: str
    description: str
    type: TemplateType
    questions: list[CreateQuestion] | None = None


class OrganisationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    allowed_domains: list[str]
    created_datetime: datetime
    updated_datetime: datetime


class OrganisationCreateRequest(BaseModel):
    name: str
    allowed_domains: list[str]


class OrganisationPatchRequest(BaseModel):
    allowed_domains: list[str]


class UserExistsResponse(BaseModel):
    exists: bool
