import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from sqlmodel import and_, func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from common.database.postgres_database import async_engine
from common.database.postgres_models import JobStatus, MinuteVersion, Recording, Transcription, User
from common.services.storage_services.audio_deletion import delete_recording_file_and_row

logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def cleanup_failed_records() -> None:
    """clear records based on each user's retention period setting."""
    logger.info("Starting stalled object cleanup process")
    cutoff_date = datetime.now(tz=ZoneInfo("Europe/London")) - timedelta(days=1)

    async with AsyncSession(async_engine) as session:
        minute_version_stmt = (
            update(MinuteVersion)
            .where(and_(MinuteVersion.created_datetime < cutoff_date, MinuteVersion.status == JobStatus.IN_PROGRESS))
            .values(status=JobStatus.FAILED, error="Unknown error. Job finalised by cleanup process")
        )
        result = await session.exec(minute_version_stmt)
        await session.commit()
        logger.info(f"updated {result.rowcount} old MinuteVersion that were not successfully processed")  # noqa: G004

    async with AsyncSession(async_engine) as session:
        transcription_stmt = (
            update(Transcription)
            .where(and_(Transcription.created_datetime < cutoff_date, Transcription.status == JobStatus.IN_PROGRESS))
            .values(status=JobStatus.FAILED, error="Unknown error. Job finalised by cleanup process")
        )
        result = await session.exec(transcription_stmt)
        await session.commit()
        logger.info(f"updated {result.rowcount} old Transcription that were not successfully processed")  # noqa: G004

    logger.info("Stalled record cleanup process completed")


async def cleanup_old_records() -> None:
    """Delete records based on each user's retention period setting."""
    logger.info("Starting data retention cleanup process")
    async with AsyncSession(async_engine) as session:
        statement = (
            select(Transcription)
            .join(User)
            .where(
                Transcription.created_datetime < func.now() - User.data_retention_days * timedelta(days=1),
            )
        )
        transcriptions = (await session.exec(statement)).all()
        logger.info("Deleting %d transcriptions.", len(transcriptions))
        for transcription in transcriptions:
            recordings = (
                await session.exec(select(Recording).where(Recording.transcription_id == transcription.id))
            ).all()
            recording_deletions = [await delete_recording_file_and_row(session, recording) for recording in recordings]
            if not all(recording_deletions):
                logger.error(
                    "Skipping deletion of transcription %s because recording deletion failed",
                    transcription.id,
                )
                continue
            await session.delete(transcription)
        await session.commit()


async def cleanup_jobs() -> None:
    await cleanup_old_records()
    await cleanup_failed_records()


async def init_cleanup_scheduler() -> None:
    """Initialize the scheduler to run cleanup at midnight, 6am, noon and 6pm (UTC)."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cleanup_jobs, "cron", hour="0,6,12,18", minute=0, timezone=UTC)
    scheduler.start()
    logger.info("cleanup scheduler initialized")
