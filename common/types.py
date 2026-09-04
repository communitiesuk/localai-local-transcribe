import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum, auto
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from common.canaries import strip_boundary_metadata
from common.constants import MAX_AGENDA_LENGTH
from common.database.postgres_models import (
    ContentSource,
    DialogueEntry,
    JobStatus,
    TemplateType,
    UserRole,
)

DOMAIN_REGEX = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z-]{0,61}[a-z]$",
    re.IGNORECASE,
)

logger = logging.getLogger(__name__)


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
    title: str | None = None


class RecordingCreateRequest(BaseModel):
    file_extension: str
    file_created_at: datetime | None = None


class RecordingCreateResponse(BaseModel):
    id: uuid.UUID
    upload_url: str


class TranscriptionCreateResponse(BaseModel):
    id: uuid.UUID


class TranscriptionConfirmResponse(BaseModel):
    id: uuid.UUID


class UpdateTranscriptionTitleRequest(BaseModel):
    title: str | None = None


class UpdateTranscriptionMetadataRequest(BaseModel):
    client_name: str | None
    case_id: str | None
    subject: str | None
    client_date_of_birth: datetime | None
    date_of_recording: datetime | None


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


type DataRetentionOptions = Literal[1, 7, 30]


class DataRetentionUpdateResponse(BaseModel):
    data_retention_days: DataRetentionOptions


class TranscriptionGetResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    dialogue_entries: list[DialogueEntry] | None
    status: JobStatus
    created_datetime: datetime
    date_of_recording: datetime | None = None
    is_upload: bool = False
    client_name: str | None
    case_id: str | None
    client_date_of_birth: datetime | None


class SingleRecording(BaseModel):
    id: uuid.UUID
    url: str
    extension: str
    created_datetime: datetime


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
    agenda: str | None = Field(description="The agenda for the meeting", default=None, max_length=MAX_AGENDA_LENGTH)


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


class FailureCategory(StrEnum):
    FACTUAL_INTEGRITY = auto()
    REQUIRED_CONTENT_AND_STRUCTURE = auto()
    EDIT_SAFETY_AND_INTENT = auto()
    DATA_PROTECTION_AND_INSTRUCTION_INTEGRITY = auto()
    EVIDENCE_AND_CITATION_QUALITY = auto()
    INPUT_SUITABILITY = auto()


class FailureMode(StrEnum):
    INVENTED_DECISION = auto()
    REVERSED_MEANING = auto()
    NO_EVIDENCE_FOR_CLAIM = auto()
    ATTRIBUTION_NOT_EVIDENCED = auto()
    NUMERIC_DATE_ERROR = auto()
    CRITICAL_OMISSION = auto()
    MISSING_ACTION = auto()
    MISSING_REQUIRED_SECTION = auto()
    UNSAFE_EDIT = auto()
    EDIT_DID_WRONG_TASK = auto()
    PERSONAL_DATA_INCLUDED = auto()
    TRANSCRIPT_INSTRUCTION_FOLLOWED = auto()
    WRONG_CITATION = auto()
    WEAK_TRANSCRIPT_SUPPORT = auto()
    SHORT_INPUT_SUMMARISED = auto()


class FailureDetail(BaseModel):
    category: FailureCategory
    mode: FailureMode
    explanation: str | None = Field(
        default=None,
        description="Specific evidence explaining this failure, e.g. a quote or reference from the transcript "
        "or minute and why it constitutes this failure mode",
    )

    _VALID_MODES_BY_CATEGORY: ClassVar[dict[FailureCategory, set[FailureMode]]] = {
        FailureCategory.FACTUAL_INTEGRITY: {
            FailureMode.INVENTED_DECISION,
            FailureMode.REVERSED_MEANING,
            FailureMode.NO_EVIDENCE_FOR_CLAIM,
            FailureMode.ATTRIBUTION_NOT_EVIDENCED,
            FailureMode.NUMERIC_DATE_ERROR,
        },
        FailureCategory.REQUIRED_CONTENT_AND_STRUCTURE: {
            FailureMode.CRITICAL_OMISSION,
            FailureMode.MISSING_ACTION,
            FailureMode.MISSING_REQUIRED_SECTION,
        },
        FailureCategory.EDIT_SAFETY_AND_INTENT: {
            FailureMode.UNSAFE_EDIT,
            FailureMode.EDIT_DID_WRONG_TASK,
        },
        FailureCategory.DATA_PROTECTION_AND_INSTRUCTION_INTEGRITY: {
            FailureMode.PERSONAL_DATA_INCLUDED,
            FailureMode.TRANSCRIPT_INSTRUCTION_FOLLOWED,
        },
        FailureCategory.EVIDENCE_AND_CITATION_QUALITY: {
            FailureMode.WRONG_CITATION,
            FailureMode.WEAK_TRANSCRIPT_SUPPORT,
        },
        FailureCategory.INPUT_SUITABILITY: {
            FailureMode.SHORT_INPUT_SUMMARISED,
        },
    }

    _CATEGORY_BY_MODE: ClassVar[dict[FailureMode, FailureCategory]] = {
        mode: category for category, modes in _VALID_MODES_BY_CATEGORY.items() for mode in modes
    }

    @model_validator(mode="after")
    def _correct_category_from_mode(self) -> "FailureDetail":
        expected_category = self._CATEGORY_BY_MODE[self.mode]
        if expected_category is None:
            logger.error("FailureMode '%s' has no known category mapping", self.mode)
        elif self.category != expected_category:
            logger.warning(
                "FailureDetail category '%s' does not match mode '%s'; correcting to '%s'",
                self.category,
                self.mode,
                expected_category,
            )
            self.category = expected_category
        return self


class GuardrailScore(BaseModel):
    score: float = Field(description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Reasoning for the score")
    categories: list[FailureDetail] = Field(description="List of failure categories that contributed to the score")


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

    def __post_init__(self) -> None:
        self.text = strip_boundary_metadata(self.text)


class MeetingType(StrEnum):
    too_short = auto()
    short = auto()
    standard = auto()


class AgendaUsage(StrEnum):
    NOT_USED = auto()
    OPTIONAL = auto()
    REQUIRED = auto()


class TranscriptionSortOrder(StrEnum):
    newest = auto()
    oldest = auto()


class TemplateMetadata(BaseModel):
    name: str
    description: str
    category: str
    agenda_usage: AgendaUsage


class CreateQuestion(BaseModel):
    position: int
    title: str
    description: str
    format_instructions: str = ""


class Question(CreateQuestion):
    id: uuid.UUID


class PatchUserTemplateRequest(BaseModel):
    name: str | None = None
    content: str | None = None
    heading: str | None = None
    description: str | None = None
    questions: list[CreateQuestion | Question] | None = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    updated_datetime: datetime
    name: str
    content: str
    heading: str
    description: str
    type: TemplateType
    questions: list[Question] | None


class CreateUserTemplateRequest(BaseModel):
    name: str
    content: str
    heading: str = ""
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

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, v: list[str]) -> list[str]:
        return validate_fqdn_list(v)


class OrganisationPatchRequest(BaseModel):
    allowed_domains: list[str]
    updated_datetime: datetime

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, v: list[str]) -> list[str]:
        return validate_fqdn_list(v)


class UserExistsResponse(BaseModel):
    exists: bool
