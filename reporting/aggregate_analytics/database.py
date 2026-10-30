from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session
from sqlmodel import create_engine

from common.database.database_credentials import (
    DbCredentialsProvider,
    IamDbCredentialsProvider,
    StaticDbCredentialsProvider,
    attach_dynamic_credentials,
)
from common.settings import Settings, get_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
QUERY_FILE = Path(__file__).parent / "analytics-event-counts.sql"
LOCAL_ENVIRONMENTS = ("local", "test")


@dataclass(frozen=True)
class EventRow:
    event_type: str
    recording_source: str | None
    organisation_id: str | None
    month: str
    count: int


def credential_provider(settings: Settings) -> DbCredentialsProvider:
    if settings.POSTGRES_USER is None:
        msg = "POSTGRES_USER must be set"
        raise ValueError(msg)
    if settings.ENVIRONMENT in LOCAL_ENVIRONMENTS:
        if settings.POSTGRES_PASSWORD is None:
            msg = "POSTGRES_PASSWORD must be set"
            raise ValueError(msg)
        return StaticDbCredentialsProvider(settings.POSTGRES_USER, settings.POSTGRES_PASSWORD)
    if settings.AWS_REGION is None:
        msg = "AWS_REGION must be set"
        raise ValueError(msg)
    return IamDbCredentialsProvider(
        db_hostname=settings.POSTGRES_HOST,
        port=settings.POSTGRES_IAM_PORT or settings.POSTGRES_PORT,
        username=settings.POSTGRES_USER,
        region_name=settings.AWS_REGION,
    )


def build_engine(settings: Settings) -> Engine:
    """Mirror common/database/postgres_database.py, optionally connecting to POSTGRES_HOSTADDR (the SSM tunnel)."""
    connect_args: dict[str, object] = {}
    if settings.POSTGRES_HOSTADDR:
        connect_args["hostaddr"] = settings.POSTGRES_HOSTADDR
    if settings.ENVIRONMENT not in LOCAL_ENVIRONMENTS:
        connect_args |= {"sslmode": "verify-full", "sslrootcert": settings.RDS_CA_BUNDLE_PATH}
    engine = create_engine(
        f"postgresql+psycopg2://{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
        connect_args=connect_args,
    )
    attach_dynamic_credentials(engine, credential_provider(settings))
    return engine


def fetch_event_rows(start: date, end: date) -> list[EventRow]:
    """Run analytics-event-counts.sql against the database configured via POSTGRES_*."""
    engine = build_engine(get_settings())
    try:
        with Session(engine) as session:
            result = session.execute(text(QUERY_FILE.read_text(encoding="utf-8")), {"start": start, "end": end})
            return [
                EventRow(
                    event_type=row.event_type,
                    recording_source=row.recording_source or None,
                    organisation_id=row.organisation_id.lower() or None,
                    month=row.month,
                    count=row.event_count,
                )
                for row in result
            ]
    finally:
        engine.dispose()


def count_rows(rows: Iterable[EventRow], event_type: str, recording_source: str | None = None) -> int:
    return sum(
        row.count
        for row in rows
        if row.event_type == event_type and (recording_source is None or row.recording_source == recording_source)
    )


def monthly_count_rows(
    rows: Iterable[EventRow], event_types: tuple[str, ...], *, by_organisation: bool
) -> dict[tuple[str | None, str], int]:
    totals: dict[tuple[str | None, str], int] = {}
    for row in rows:
        if row.event_type in event_types:
            key = (row.organisation_id if by_organisation else None, row.month)
            totals[key] = totals.get(key, 0) + row.count
    return totals
