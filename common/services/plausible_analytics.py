import logging
from uuid import UUID

from common.services.plausible_client import plausible_client
from common.types import AnalyticsEventName

logger = logging.getLogger(__name__)


async def record_event(
    name: AnalyticsEventName,
    user_agent: str,
    client_ip: str | None,
    organisation_id: UUID | None = None,
) -> None:
    """Send an aggregate event to Plausible. Nothing is stored against a user, and nothing is recorded locally."""
    if not plausible_client:
        return

    try:
        await plausible_client.send_event(
            name,
            str(organisation_id) if organisation_id else None,
            user_agent,
            client_ip,
        )
    except Exception:
        logger.exception("Failed to record analytics event %s", name)
