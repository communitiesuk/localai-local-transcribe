import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from backend.api.dependencies import SQLSessionDep, UserDep
from backend.services.analytics import record_user_analytics_event
from backend.utils.queries import has_pending_minute_version_for_transcription
from common.database.postgres_models import (
    AnalyticsEventMetadata,
    AnalyticsEventType,
    ContentSource,
    GuardrailResult,
    JobStatus,
    Minute,
    MinuteVersion,
    SummaryEditType,
    Transcription,
    User,
)
from common.guardrail_messages import get_guardrail_warning_message_for_results
from common.services.queue_services import get_queue_service
from common.settings import get_settings
from common.types import (
    EditMessageData,
    GuardrailWarningResponse,
    MinuteListItem,
    MinutesCreateRequest,
    MinuteVersionCreateRequest,
    MinuteVersionResponse,
    SummaryInteractionEventRequest,
    SummaryInteractionEventType,
    TaskType,
    WorkerMessage,
)

settings = get_settings()

llm_queue_service = get_queue_service(
    settings.QUEUE_SERVICE_NAME, settings.LLM_QUEUE_NAME, settings.LLM_DEADLETTER_QUEUE_NAME
)

minutes_router = APIRouter(tags=["Minutes"])

# An initial generation is not an edit, so it emits no SUMMARY_EDIT_SUBMITTED event.
SUMMARY_EDIT_TYPE_BY_CONTENT_SOURCE = {
    ContentSource.MANUAL_EDIT: SummaryEditType.MANUAL,
    ContentSource.AI_EDIT: SummaryEditType.AI,
}

# Maps the closed set of client-reportable events onto the stored event types.
ANALYTICS_EVENT_TYPE_BY_SUMMARY_INTERACTION = {
    SummaryInteractionEventType.SUMMARY_DOWNLOADED: AnalyticsEventType.SUMMARY_DOWNLOADED,
    SummaryInteractionEventType.SUMMARY_COPIED: AnalyticsEventType.SUMMARY_COPIED,
}


async def _record_summary_analytics_event(
    user: User,
    event_type: AnalyticsEventType,
    transcription_id: uuid.UUID,
    minute_version_id: uuid.UUID,
    *,
    source_id: uuid.UUID | None = None,
    extra_metadata: AnalyticsEventMetadata | None = None,
) -> None:
    """Record a summary analytics event, mirroring `_record_transcription_edit_analytics_event`.

    Deliberately takes no session: `record_user_analytics_event` uses one of its own, so a failure here cannot
    roll back the request or stop the work that follows the call.
    """
    event_metadata: AnalyticsEventMetadata = {
        "transcription_id": str(transcription_id),
        "minute_version_id": str(minute_version_id),
    }
    if extra_metadata:
        event_metadata.update(extra_metadata)

    await record_user_analytics_event(
        user,
        event_type,
        transcription_id=transcription_id,
        source_id=source_id,
        event_metadata=event_metadata,
    )


@minutes_router.get("/transcription/{transcription_id}/minutes")
async def list_minutes_for_transcription(
    transcription_id: uuid.UUID, session: SQLSessionDep, user: UserDep
) -> list[MinuteListItem]:
    transcription = await session.get(Transcription, transcription_id)
    if not transcription or transcription.user_id != user.id:
        raise HTTPException(404, "Not found")

    query = (
        select(Minute).where(Minute.transcription_id == transcription_id).order_by(col(Minute.created_datetime).asc())
    )
    result = await session.exec(query)
    minutes = result.all()
    return [
        MinuteListItem(
            id=minute.id,
            created_datetime=minute.created_datetime,
            updated_datetime=minute.updated_datetime,
            transcription_id=minute.transcription_id,
            template_name=minute.template_name,
            agenda=minute.agenda,
        )
        for minute in minutes
    ]


@minutes_router.post("/transcription/{transcription_id}/minutes")
async def create_minute(
    transcription_id: uuid.UUID, request: MinutesCreateRequest, session: SQLSessionDep, user: UserDep
) -> MinuteVersionResponse:
    transcription = await session.get(Transcription, transcription_id)
    if not transcription or transcription.user_id != user.id:
        raise HTTPException(404, "Not found")

    pending_minute_version = await has_pending_minute_version_for_transcription(session, transcription_id)
    if pending_minute_version:
        raise HTTPException(
            status_code=409,
            detail="A document is already being created for this transcript",
        )

    minute = Minute(
        transcription_id=transcription_id,
        template_name=request.template_name,
        agenda=request.agenda,
        user_template_id=request.template_id,
    )
    session.add(minute)
    minute_version = MinuteVersion(id=uuid.uuid4(), minute_id=minute.id)
    session.add(minute_version)
    await session.commit()
    await session.refresh(minute_version)

    # Publish before recording analytics, and keep this line as close to the commit above as possible. The
    # version is committed at AWAITING_START, which has_pending_minute_version_for_transcription treats as in
    # flight and cleanup_failed_records does not rescue - it only picks up rows at IN_PROGRESS. So if the process
    # dies between the commit and this line (a deploy cancellation, a client disconnect) the row stays
    # AWAITING_START forever and the user can never generate a summary for this transcript again. Any await
    # placed before this line widens that window, and a lost analytics event only costs a row in a report.
    llm_queue_service.publish_message(WorkerMessage(id=minute_version.id, type=TaskType.MINUTE))

    # The worker records SUMMARY_RECEIVED with this same source_id once generation finishes (see
    # minute_handler_service), so a report can match request to receipt on source_id and subtract the two
    # occurred_datetimes to get generation latency. Without a shared key it would have to infer which receipt
    # belongs to which request from how close their timestamps happen to be.
    await _record_summary_analytics_event(
        user,
        AnalyticsEventType.SUMMARY_REQUESTED,
        transcription_id=transcription_id,
        minute_version_id=minute_version.id,
        source_id=minute_version.id,
    )

    return MinuteVersionResponse(
        id=minute_version.id,
        minute_id=minute.id,
        status=minute_version.status,
        created_datetime=minute_version.created_datetime,
        error=minute_version.error,
        ai_edit_instructions=minute_version.ai_edit_instructions,
        html_content=minute_version.html_content,
        content_source=minute_version.content_source,
    )


@minutes_router.get("/minutes/{minutes_id}")
async def get_minute(minutes_id: uuid.UUID, session: SQLSessionDep, user: UserDep) -> Minute:
    query = (
        select(Minute)
        .where(Minute.id == minutes_id)
        .options(selectinload(Minute.transcription), selectinload(Minute.minute_versions))
    )
    result = await session.exec(query)
    minute = result.first()
    if not minute or not minute.transcription.user_id or minute.transcription.user_id != user.id:
        raise HTTPException(404, "Not found")

    return minute


@minutes_router.get("/minutes/{minute_id}/versions")
async def list_minute_versions(
    minute_id: uuid.UUID, session: SQLSessionDep, user: UserDep
) -> list[MinuteVersionResponse]:
    result = await session.exec(
        select(Minute)
        .where(Minute.id == minute_id)
        .options(
            selectinload(Minute.minute_versions),
            selectinload(Minute.transcription),
        )
    )
    minute = result.first()
    if not minute or not minute.transcription.user_id or minute.transcription.user_id != user.id:
        raise HTTPException(404)

    word_count = sum(len(entry["text"].split()) for entry in (minute.transcription.dialogue_entries or []))
    is_too_short = word_count < settings.MIN_WORD_COUNT_FOR_SUMMARY

    return [
        MinuteVersionResponse(
            id=version.id,
            minute_id=minute_id,
            status=version.status,
            created_datetime=version.created_datetime,
            error=version.error,
            ai_edit_instructions=version.ai_edit_instructions,
            html_content=version.html_content,
            content_source=version.content_source,
            too_short=is_too_short,
        )
        for version in minute.minute_versions
    ]


@minutes_router.post("/minutes/{minute_id}/versions")
async def create_minute_version(
    minute_id: uuid.UUID, request: MinuteVersionCreateRequest, session: SQLSessionDep, user: UserDep
) -> MinuteVersionResponse:
    minute = await get_minute(minute_id, session, user)
    minute_version = MinuteVersion(
        id=uuid.uuid4(),
        minute_id=minute.id,
        content_source=request.content_source,
        html_content=request.html_content,
        ai_edit_instructions=request.ai_edit_instructions.instruction if request.ai_edit_instructions else None,
        status=JobStatus.AWAITING_START if request.ai_edit_instructions else JobStatus.COMPLETED,
    )
    minute.updated_datetime = datetime.now(tz=UTC)
    session.add(minute_version)
    await session.commit()
    await session.refresh(minute_version)

    # Publish first, for the reason given in create_minute: an AI-edit version is committed at AWAITING_START,
    # so a version that is never queued renders as perpetually generating and blocks the transcript's 409 guard.
    if request.ai_edit_instructions:
        llm_queue_service.publish_message(
            WorkerMessage(
                id=minute_version.id,
                data=EditMessageData(source_id=request.ai_edit_instructions.source_id),
                type=TaskType.EDIT,
            )
        )

    edit_type = SUMMARY_EDIT_TYPE_BY_CONTENT_SOURCE.get(request.content_source)
    if edit_type is not None:
        await _record_summary_analytics_event(
            user,
            AnalyticsEventType.SUMMARY_EDIT_SUBMITTED,
            transcription_id=minute.transcription_id,
            minute_version_id=minute_version.id,
            source_id=minute_version.id,
            # SummaryEditType is a StrEnum, so this serialises to the same JSON as edit_type.value
            extra_metadata={"edit_type": edit_type},
        )

    return MinuteVersionResponse(
        id=minute_version.id,
        minute_id=minute_id,
        status=minute_version.status,
        created_datetime=minute_version.created_datetime,
        error=minute_version.error,
        ai_edit_instructions=minute_version.ai_edit_instructions,
        html_content=minute_version.html_content,
        content_source=minute_version.content_source,
    )


@minutes_router.get("/minute_versions/{minute_version_id}")
async def get_minute_version(minute_version_id: uuid.UUID, session: SQLSessionDep, user: UserDep) -> MinuteVersion:
    query = (
        select(MinuteVersion)
        .where(MinuteVersion.id == minute_version_id)
        .options(selectinload(MinuteVersion.minute).selectinload(Minute.transcription))
    )
    minute_version = (await session.exec(query)).first()
    if (
        not minute_version
        or not minute_version.minute.transcription.user_id
        or minute_version.minute.transcription.user_id != user.id
    ):
        raise HTTPException(404, "Not found")

    return minute_version


@minutes_router.get("/minute_versions/{minute_version_id}/guardrails")
async def get_guardrail_warning(
    minute_version_id: uuid.UUID, session: SQLSessionDep, _user: UserDep
) -> GuardrailWarningResponse:
    query = (
        select(MinuteVersion)
        .where(MinuteVersion.id == minute_version_id)
        .options(
            selectinload(MinuteVersion.guardrail_results).selectinload(GuardrailResult.failure_categories),
            selectinload(MinuteVersion.minute).selectinload(Minute.transcription),
        )
    )
    minute_version = (await session.exec(query)).first()
    if not minute_version or not minute_version.minute.transcription.user_id:
        raise HTTPException(404, "Not found")

    return GuardrailWarningResponse(
        message=get_guardrail_warning_message_for_results(
            content_source=minute_version.content_source,
            guardrail_results=minute_version.guardrail_results,
        )
    )


@minutes_router.post("/minute_versions/{minute_version_id}/analytics-events", status_code=204)
async def record_summary_interaction_event(
    minute_version_id: uuid.UUID,
    request: SummaryInteractionEventRequest,
    session: SQLSessionDep,
    user: UserDep,
) -> None:
    """Record a summary interaction that only the client can observe (download, copy).

    No `source_id`: a user may legitimately download or copy the same version repeatedly, and each of those is a
    real event rather than a retry. `record_user_analytics_event` swallows its own failures, so this returns 204
    even if the insert fails - the client is never given a reason to retry or to surface an error.
    """
    minute_version = await get_minute_version(minute_version_id, session, user)

    await _record_summary_analytics_event(
        user,
        ANALYTICS_EVENT_TYPE_BY_SUMMARY_INTERACTION[request.event_type],
        transcription_id=minute_version.minute.transcription_id,
        minute_version_id=minute_version.id,
        extra_metadata={"copy_type": request.copy_type} if request.copy_type else None,
    )


@minutes_router.delete("/minute_versions/{minute_version_id}")
async def delete_minute_version(minute_version_id: uuid.UUID, session: SQLSessionDep, user: UserDep) -> None:
    query = (
        select(MinuteVersion)
        .where(MinuteVersion.id == minute_version_id)
        .options(
            selectinload(MinuteVersion.minute).selectinload(Minute.transcription),
        )
    )
    minute_version = (await session.exec(query)).first()
    if (
        not minute_version
        or not minute_version.minute.transcription.user_id
        or minute_version.minute.transcription.user_id != user.id
    ):
        raise HTTPException(404, "Not found")

    minute = minute_version.minute
    should_delete_minute = False
    if minute_version.status == JobStatus.FAILED:
        await session.exec(select(Minute.id).where(Minute.id == minute.id).with_for_update())
        sibling_result = await session.exec(
            select(MinuteVersion.id)
            .where(MinuteVersion.minute_id == minute.id)
            .where(MinuteVersion.id != minute_version.id)
            .limit(1)
        )
        should_delete_minute = sibling_result.first() is None

    await session.delete(minute if should_delete_minute else minute_version)
    await session.commit()
