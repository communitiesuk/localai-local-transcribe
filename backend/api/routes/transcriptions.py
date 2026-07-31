import logging
import math
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import not_, or_
from sqlmodel import col, func, select

from backend.api.dependencies import SQLSessionDep, UserDep
from backend.utils.get_file_s3_key import get_file_s3_key
from common.database.postgres_models import (
    DialogueEntry,
    Minute,
    MinuteVersion,
    Recording,
    Transcription,
)
from common.services.queue_services import get_queue_service
from common.services.storage_services import get_storage_service
from common.settings import get_settings
from common.types import (
    LabelledTranscriptionMetadata,
    LabelledTranscriptionsResponse,
    RecordingCreateRequest,
    RecordingCreateResponse,
    RecordingSortOrder,
    RenameSpeakerRequest,
    SingleRecording,
    TaskType,
    TranscriptionCreateRequest,
    TranscriptionCreateResponse,
    TranscriptionGetResponse,
    UnlabelledTranscriptionMetadata,
    UnlabelledTranscriptionsResponse,
    UpdateDialogueEntrySpeakerRequest,
    UpdateDialogueEntryTextRequest,
    UpdateTranscriptionTitleRequest,
    WorkerMessage,
)

settings = get_settings()

storage_service = get_storage_service(settings.STORAGE_SERVICE_NAME)


transcriptions_router = APIRouter(tags=["Transcriptions"])
transcription_queue_service = get_queue_service(
    settings.QUEUE_SERVICE_NAME, settings.TRANSCRIPTION_QUEUE_NAME, settings.TRANSCRIPTION_DEADLETTER_QUEUE_NAME
)

logger = logging.getLogger(__name__)


async def _get_owned_transcription_or_404(
    session: SQLSessionDep,
    transcription_id: uuid.UUID,
    current_user: UserDep,
) -> Transcription:
    transcription = await session.get(Transcription, transcription_id)
    if not transcription or transcription.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return transcription


def _get_dialogue_entries(transcription: Transcription) -> list[DialogueEntry]:
    return list(transcription.dialogue_entries or [])


def _get_dialogue_entry_or_404(dialogue_entries: list[DialogueEntry], entry_index: int) -> DialogueEntry:
    if entry_index < 0 or entry_index >= len(dialogue_entries):
        raise HTTPException(status_code=404, detail="Dialogue entry not found")
    return dialogue_entries[entry_index]


def _validate_dialogue_entry(
    entry: DialogueEntry,
    *,
    expected_speaker: str | None = None,
    expected_start_time: float | None = None,
    expected_end_time: float | None = None,
    expected_text: str | None = None,
) -> None:
    if expected_speaker is not None and entry["speaker"] != expected_speaker:
        raise HTTPException(status_code=409, detail="Dialogue entry speaker has changed")
    if expected_start_time is not None and entry["start_time"] != expected_start_time:
        raise HTTPException(status_code=409, detail="Dialogue entry start time has changed")
    if expected_end_time is not None and entry["end_time"] != expected_end_time:
        raise HTTPException(status_code=409, detail="Dialogue entry end time has changed")
    if expected_text is not None and entry["text"] != expected_text:
        raise HTTPException(status_code=409, detail="Dialogue entry text has changed")


<<<<<<< HEAD
def _created_datetime_order(sort: RecordingSortOrder):
    column = col(Transcription.created_datetime)
    return column.asc() if sort == RecordingSortOrder.oldest else column.desc()


=======
>>>>>>> origin/development
@transcriptions_router.get("/transcriptions/labelled", response_model=LabelledTranscriptionsResponse)
async def list_labelled_transcriptions(
    session: SQLSessionDep,
    current_user: UserDep,
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
<<<<<<< HEAD
    sort: Annotated[RecordingSortOrder, Query(description="Sort order for date recorded")] = RecordingSortOrder.newest,
=======
>>>>>>> origin/development
) -> LabelledTranscriptionsResponse:
    """Get paginated metadata for labelled transcriptions for the current user."""
    labelled_filter = or_(
        col(Transcription.title).is_not(None),
        col(Transcription.client_date_of_birth).is_not(None),
        col(Transcription.client_name).is_not(None),
        col(Transcription.case_id).is_not(None),
    )

    count_statement = (
        select(func.count(col(Transcription.id))).where(Transcription.user_id == current_user.id).where(labelled_filter)
    )
    count_result = await session.exec(count_statement)
    total_count = count_result.one()

    offset = (page - 1) * page_size
    statement = (
        select(Transcription)
        .where(Transcription.user_id == current_user.id)
        .where(labelled_filter)
<<<<<<< HEAD
        .order_by(_created_datetime_order(sort))
=======
        .order_by(col(Transcription.created_datetime).desc())
>>>>>>> origin/development
        .offset(offset)
        .limit(page_size)
    )
    result = await session.exec(statement)
    transcriptions = result.all()

    items = [
        LabelledTranscriptionMetadata(
<<<<<<< HEAD
            id=t.id,
            created_datetime=t.created_datetime,
            title=t.title,
            text=t.dialogue_entries[0]["text"][:100] if t.dialogue_entries else "",
            status=t.status,
            date_of_recording=t.date_of_recording,
            client_date_of_birth=t.client_date_of_birth,
            client_name=t.client_name,
            case_id=t.case_id,
        )
        for t in transcriptions
    ]

    total_pages = math.ceil(total_count / page_size) or 1

    return LabelledTranscriptionsResponse(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@transcriptions_router.get("/transcriptions/unlabelled", response_model=UnlabelledTranscriptionsResponse)
async def list_unlabelled_transcriptions(
    session: SQLSessionDep,
    current_user: UserDep,
    sort: Annotated[RecordingSortOrder, Query(description="Sort order for date recorded")] = RecordingSortOrder.newest,
) -> UnlabelledTranscriptionsResponse:
    """Get metadata for unlabelled transcriptions for the current user."""
    labelled_filter = or_(
        col(Transcription.title).is_not(None),
        col(Transcription.client_date_of_birth).is_not(None),
        col(Transcription.client_name).is_not(None),
        col(Transcription.case_id).is_not(None),
    )

    count_statement = (
        select(func.count(col(Transcription.id)))
        .where(Transcription.user_id == current_user.id)
        .where(not_(labelled_filter))
    )
    count_result = await session.exec(count_statement)
    total_count = count_result.one()

    statement = (
        select(Transcription)
        .where(Transcription.user_id == current_user.id)
        .where(not_(labelled_filter))
        .order_by(_created_datetime_order(sort))
    )
    result = await session.exec(statement)
    transcriptions = result.all()

    items = [
        UnlabelledTranscriptionMetadata(
=======
>>>>>>> origin/development
            id=t.id,
            created_datetime=t.created_datetime,
            title=t.title,
            text=t.dialogue_entries[0]["text"][:100] if t.dialogue_entries else "",
            status=t.status,
            date_of_recording=t.date_of_recording,
            client_date_of_birth=t.client_date_of_birth,
            client_name=t.client_name,
            case_id=t.case_id,
        )
        for t in transcriptions
    ]

    total_pages = math.ceil(total_count / page_size) or 1

    return LabelledTranscriptionsResponse(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@transcriptions_router.get("/transcriptions/unlabelled", response_model=UnlabelledTranscriptionsResponse)
async def list_unlabelled_transcriptions(
    session: SQLSessionDep,
    current_user: UserDep,
) -> UnlabelledTranscriptionsResponse:
    """Get metadata for unlabelled transcriptions for the current user."""
    labelled_filter = or_(
        col(Transcription.title).is_not(None),
        col(Transcription.client_date_of_birth).is_not(None),
        col(Transcription.client_name).is_not(None),
        col(Transcription.case_id).is_not(None),
    )

    count_statement = (
        select(func.count(col(Transcription.id)))
        .where(Transcription.user_id == current_user.id)
        .where(not_(labelled_filter))
    )
    count_result = await session.exec(count_statement)
    total_count = count_result.one()

    statement = (
        select(Transcription)
        .where(Transcription.user_id == current_user.id)
        .where(not_(labelled_filter))
        .order_by(col(Transcription.created_datetime).desc())
    )
    result = await session.exec(statement)
    transcriptions = result.all()

    items = [
        UnlabelledTranscriptionMetadata(
            id=t.id,
            date_of_recording=t.date_of_recording,
            title=t.title,
            text=t.dialogue_entries[0]["text"][:100] if t.dialogue_entries else "",
            status=t.status,
        )
        for t in transcriptions
    ]

    return UnlabelledTranscriptionsResponse(
        items=items,
        total_count=total_count,
    )


@transcriptions_router.post("/recordings")
async def create_recording(
    request: RecordingCreateRequest, session: SQLSessionDep, user: UserDep
) -> RecordingCreateResponse:
    recording_id = uuid.uuid4()
    file_name = f"{recording_id}.{request.file_extension}"
    user_upload_s3_file_key = get_file_s3_key(user.email, file_name)
    recording = Recording(user_id=user.id, s3_file_key=user_upload_s3_file_key)
    session.add(recording)
    await session.commit()
    presigned_url = await storage_service.generate_presigned_url_put_object(user_upload_s3_file_key, 3600)
    await session.refresh(recording)
    return RecordingCreateResponse(id=recording.id, upload_url=presigned_url)


@transcriptions_router.post("/transcriptions", response_model=TranscriptionCreateResponse, status_code=201)
async def create_transcription(
    request: TranscriptionCreateRequest,
    session: SQLSessionDep,
    current_user: UserDep,
) -> TranscriptionCreateResponse:
    """Start a transcription job."""
    recording = await session.get(Recording, request.recording_id)
    if not recording or recording.user_id != current_user.id:
        raise HTTPException(404, detail="Recording not found")
    transcription = Transcription(user_id=current_user.id, title=request.title)

    if not await storage_service.check_object_exists(recording.s3_file_key):
        raise HTTPException(
            status_code=404,
            detail=f"Recording file not found in S3: {recording.s3_file_key}",
        )

    minute = Minute(
        template_name=request.template_name,
        user_template_id=request.template_id,
        agenda=request.agenda,
        transcription_id=transcription.id,
    )
    minute_version = MinuteVersion(minute_id=minute.id)
    session.add(transcription)
    session.add(minute)
    session.add(minute_version)
    recording.transcription_id = transcription.id
    await session.commit()
    transcription_queue_service.publish_message(WorkerMessage(id=minute.id, type=TaskType.TRANSCRIPTION))

    return TranscriptionCreateResponse(id=transcription.id)


@transcriptions_router.get("/transcriptions/{transcription_id}", response_model=TranscriptionGetResponse)
async def get_transcription(
    transcription_id: uuid.UUID,
    session: SQLSessionDep,
    current_user: UserDep,
) -> TranscriptionGetResponse:
    """Get a specific transcription by ID."""
    transcription = await _get_owned_transcription_or_404(session, transcription_id, current_user)
    return TranscriptionGetResponse(
        id=transcription.id,
        status=transcription.status,
        dialogue_entries=transcription.dialogue_entries,
        title=transcription.title,
        created_datetime=transcription.created_datetime,
    )


@transcriptions_router.get("/transcriptions/{transcription_id}/recordings")
async def get_recordings_for_transcription(
    transcription_id: uuid.UUID, session: SQLSessionDep, user: UserDep
) -> list[SingleRecording]:
    transcription = await session.get(Transcription, transcription_id)
    if not transcription or transcription.user_id != user.id:
        raise HTTPException(404)

    result = await session.exec(
        select(Recording)
        .where(Recording.transcription_id == transcription.id)
        .order_by(col(Recording.created_datetime).desc())
    )
    recordings = result.all()
    # Only return oldest of each file type
    # So users only see original mp3 file if it was converted due to multiple channels
    unique_recordings = {Path(recording.s3_file_key).suffix: recording for recording in recordings}.values()
    signed_recordings: list[SingleRecording] = []
    for recording in unique_recordings:
        if not await storage_service.check_object_exists(recording.s3_file_key):
            continue
        key_path = Path(recording.s3_file_key)
        filename = f"{transcription.title}{key_path.suffix}" if transcription.title else key_path.name
        presigned_url = await storage_service.generate_presigned_url_get_object(
            recording.s3_file_key, filename, 60 * 60 * 12
        )
        signed_recordings.append(SingleRecording(id=recording.id, url=presigned_url, extension=key_path.suffix))

    return signed_recordings


@transcriptions_router.patch("/transcriptions/{transcription_id}/title", status_code=204)
async def update_transcription_title(
    transcription_id: uuid.UUID,
    request: UpdateTranscriptionTitleRequest,
    session: SQLSessionDep,
    current_user: UserDep,
) -> None:
    """Update a transcription title."""
    transcription = await _get_owned_transcription_or_404(session, transcription_id, current_user)
    if request.title is not None:
        transcription.title = request.title
        await session.commit()


@transcriptions_router.patch("/transcriptions/{transcription_id}/speakers", status_code=204)
async def rename_speaker_everywhere(
    transcription_id: uuid.UUID,
    request: RenameSpeakerRequest,
    session: SQLSessionDep,
    current_user: UserDep,
) -> None:
    transcription = await _get_owned_transcription_or_404(session, transcription_id, current_user)
    dialogue_entries = _get_dialogue_entries(transcription)

    transcription.dialogue_entries = [
        {
            "text": entry["text"],
            "start_time": entry["start_time"],
            "end_time": entry["end_time"],
            "speaker": request.new_speaker if entry["speaker"] == request.original_speaker else entry["speaker"],
        }
        for entry in dialogue_entries
    ]
    await session.commit()


@transcriptions_router.patch(
    "/transcriptions/{transcription_id}/dialogue-entries/{entry_index}/speaker", status_code=204
)
async def update_dialogue_entry_speaker(
    transcription_id: uuid.UUID,
    entry_index: int,
    request: UpdateDialogueEntrySpeakerRequest,
    session: SQLSessionDep,
    current_user: UserDep,
) -> None:
    transcription = await _get_owned_transcription_or_404(session, transcription_id, current_user)
    dialogue_entries = _get_dialogue_entries(transcription)
    existing_entry = _get_dialogue_entry_or_404(dialogue_entries, entry_index)
    _validate_dialogue_entry(
        existing_entry,
        expected_speaker=request.expected_speaker,
        expected_start_time=request.expected_start_time,
        expected_end_time=request.expected_end_time,
    )

    transcription.dialogue_entries = [
        {
            "text": entry["text"],
            "start_time": entry["start_time"],
            "end_time": entry["end_time"],
            "speaker": request.new_speaker if index == entry_index else entry["speaker"],
        }
        for index, entry in enumerate(dialogue_entries)
    ]
    await session.commit()


@transcriptions_router.patch("/transcriptions/{transcription_id}/dialogue-entries/{entry_index}/text", status_code=204)
async def update_dialogue_entry_text(
    transcription_id: uuid.UUID,
    entry_index: int,
    request: UpdateDialogueEntryTextRequest,
    session: SQLSessionDep,
    current_user: UserDep,
) -> None:
    transcription = await _get_owned_transcription_or_404(session, transcription_id, current_user)
    dialogue_entries = _get_dialogue_entries(transcription)
    existing_entry = _get_dialogue_entry_or_404(dialogue_entries, entry_index)
    _validate_dialogue_entry(
        existing_entry,
        expected_text=request.expected_text,
        expected_speaker=request.expected_speaker,
        expected_start_time=request.expected_start_time,
        expected_end_time=request.expected_end_time,
    )

    transcription.dialogue_entries = [
        {
            "speaker": entry["speaker"],
            "start_time": entry["start_time"],
            "end_time": entry["end_time"],
            "text": request.new_text if index == entry_index else entry["text"],
        }
        for index, entry in enumerate(dialogue_entries)
    ]
    await session.commit()


@transcriptions_router.delete("/transcriptions/{transcription_id}", status_code=204)
async def delete_transcription(transcription_id: uuid.UUID, session: SQLSessionDep, current_user: UserDep) -> None:
    """Delete a specific transcription by ID."""
    # First check if the transcription exists and belongs to the user
    transcription = await _get_owned_transcription_or_404(session, transcription_id, current_user)

    # Delete the transcription
    await session.delete(transcription)
    await session.commit()
