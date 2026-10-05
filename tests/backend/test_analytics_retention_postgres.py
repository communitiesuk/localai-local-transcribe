"""Optional PostgreSQL checks; set ANALYTICS_RETENTION_TEST_DATABASE_URL to run."""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import func, insert, literal, select, text
from sqlalchemy.ext.asyncio import create_async_engine

from backend import cleanup_job
from common.database.postgres_models import AnalyticsEvent, AnalyticsEventType


@pytest_asyncio.fixture
async def analytics_engine(monkeypatch):
    url = os.environ.get("ANALYTICS_RETENTION_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set ANALYTICS_RETENTION_TEST_DATABASE_URL for isolated PostgreSQL tests")
    schema = f"analytics_retention_test_{uuid4().hex}"
    admin_engine = create_async_engine(url)
    async with admin_engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as connection:
            await connection.run_sync(lambda conn: AnalyticsEvent.__table__.create(conn))
        monkeypatch.setattr(cleanup_job, "async_engine", engine)
        yield engine
    finally:
        await engine.dispose()
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin_engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("now", "cutoff"),
    [
        (datetime(2024, 2, 29, 12, tzinfo=UTC), datetime(2023, 2, 28, 12, tzinfo=UTC)),
        (datetime(2025, 2, 28, 12, tzinfo=UTC), datetime(2024, 2, 28, 12, tzinfo=UTC)),
        (datetime(2025, 3, 31, 0, 30, tzinfo=UTC), datetime(2024, 3, 31, 0, 30, tzinfo=UTC)),
    ],
)
@pytest.mark.parametrize("timezone", ["UTC", "Europe/London", "America/New_York"])
async def test_analytics_retention_calendar_boundary(analytics_engine, monkeypatch, now, cutoff, timezone):
    monkeypatch.setattr(
        cleanup_job,
        "func",
        SimpleNamespace(timezone=func.timezone, now=lambda: literal(now)),
    )
    # Force the cleanup connection's session timezone to verify the cutoff stays in UTC.
    from sqlalchemy import event

    @event.listens_for(analytics_engine.sync_engine, "checkout")
    def set_timezone(dbapi_connection, _record, _proxy):
        cursor = dbapi_connection.cursor()
        cursor.execute(f"SET TIME ZONE '{timezone}'")
        cursor.close()

    times = {
        "expired": cutoff - timedelta(microseconds=1),
        "boundary": cutoff,
        "retained": cutoff + timedelta(microseconds=1),
        "recent": now,
    }
    async with analytics_engine.begin() as connection:
        await connection.execute(
            insert(AnalyticsEvent),
            [
                {
                    "id": uuid4(),
                    "occurred_datetime": occurred,
                    "event_type": AnalyticsEventType.USER_INVITED,
                    "evaluation_id": label,
                }
                for label, occurred in times.items()
            ],
        )
    await cleanup_job.cleanup_analytics_events()
    await cleanup_job.cleanup_analytics_events()
    async with analytics_engine.connect() as connection:
        remaining = (await connection.execute(select(AnalyticsEvent.evaluation_id))).scalars().all()
    assert set(remaining) == {"retained", "recent"}


@pytest.mark.asyncio
async def test_analytics_retention_concurrent_runs(analytics_engine):
    async with analytics_engine.begin() as connection:
        now = (await connection.execute(select(func.now()))).scalar_one()
        await connection.execute(
            insert(AnalyticsEvent),
            [
                {
                    "id": uuid4(),
                    "occurred_datetime": now - timedelta(days=400),
                    "event_type": AnalyticsEventType.USER_INVITED,
                    "evaluation_id": "expired",
                }
                for _ in range(100)
            ] + [
                {
                    "id": uuid4(),
                    "occurred_datetime": now,
                    "event_type": AnalyticsEventType.USER_INVITED,
                    "evaluation_id": "recent",
                },
            ],
        )
    async with analytics_engine.connect() as blocker:
        transaction = await blocker.begin()
        await blocker.execute(select(AnalyticsEvent.id).with_for_update())
        tasks = [asyncio.create_task(cleanup_job.cleanup_analytics_events()) for _ in range(2)]
        try:
            await asyncio.sleep(0.1)
            assert all(not task.done() for task in tasks)
            await transaction.rollback()
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=10)
        finally:
            await transaction.rollback()
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    async with analytics_engine.connect() as connection:
        remaining = (await connection.execute(select(AnalyticsEvent.evaluation_id))).scalars().all()
    assert remaining == ["recent"]
