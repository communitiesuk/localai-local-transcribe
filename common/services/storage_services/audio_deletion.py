import logging

from sqlmodel.ext.asyncio.session import AsyncSession

from common.database.postgres_models import Recording
from common.services.storage_services import get_storage_service
from common.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
storage_service = get_storage_service(settings.STORAGE_SERVICE_NAME)


async def delete_recording_file_and_row(session: AsyncSession, recording: Recording) -> bool:
    try:
        exists = await storage_service.check_object_exists(recording.s3_file_key)
        if exists:
            await storage_service.delete(recording.s3_file_key)
    except Exception as e:  # noqa: BLE001
        logger.error("Error deleting recording %s. Will keep record in database: %s", recording.id, e)
        return False
    await session.delete(recording)
    return True
