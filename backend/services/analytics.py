import asyncio
import logging
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from backend.utils.queries import get_original_recording_id
from common.database.postgres_database import async_engine
from common.database.postgres_models import AnalyticsEventMetadata, AnalyticsEventType, User
from common.services.analytics_service import record_analytics_event

logger = logging.getLogger(__name__)

# This runs inline on a request the user is waiting on, and it takes a second connection from the pool the
# request itself is using. A saturated pool would otherwise block here for the engine's pool_timeout - 60
# seconds - to record a row in a report. Giving up is the better trade. A timeout mid-commit may still land the
# insert; for events that carry a source_id the unique constraint makes that harmless, and for the rest a
# duplicate is less costly than the wait.
EVENT_TIMEOUT_SECONDS = 5


async def record_user_analytics_event(
    user: User,
    event_type: AnalyticsEventType,
    *,
    transcription_id: uuid.UUID | None = None,
    source_id: uuid.UUID | None = None,
    event_metadata: AnalyticsEventMetadata | None = None,
) -> None:
    """Record an analytics event for a user action on a session of its own, and never raise.

    Analytics is a side effect of a request, not part of it, so it must not be able to fail the action the user
    asked for. Sharing the request session allowed two ways for it to do exactly that:

    - `record_analytics_event` rolls its session back when an insert fails. On the request session that expires
      every ORM object loaded in the request, so a route that still had to read one - to build its response, say -
      hit MissingGreenlet on the next attribute access.
    - the recording lookup is a query of its own and can fail on its own, which raised straight out of the route
      and skipped whatever came after the call. In `create_minute` that was the queue publication, leaving a
      committed MinuteVersion that no worker would ever pick up and that `has_pending_minute_version_for_transcription`
      then treated as in-flight, so the user could not retry.

    Giving the lookup and the insert a separate session, and swallowing anything they raise, keeps both inside
    this function. `recording_id` is resolved so reporting can join recording -> transcript -> summary on a single
    column, rather than through `transcription`, which is deleted on a shorter retention schedule than analytics
    events.
    """
    try:
        async with asyncio.timeout(EVENT_TIMEOUT_SECONDS), AsyncSession(async_engine) as session:
            recording_id = (
                await get_original_recording_id(session, transcription_id)
                if user.evaluation_id and transcription_id
                else None
            )
            await record_analytics_event(
                session,
                event_type,
                user.evaluation_id,
                user.organisation_id,
                recording_id=recording_id,
                source_id=source_id,
                event_metadata=event_metadata,
            )
    except Exception:
        logger.exception("Failed to record %s analytics event", event_type)
