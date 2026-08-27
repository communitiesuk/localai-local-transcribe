import datetime
from typing import Any, cast

from sqlalchemy import ColumnElement, and_, or_
from sqlmodel import col, func

from common.database.postgres_models import Transcription


def _date_part_filters(
    column: ColumnElement[Any],
    *,
    day: int | None = None,
    month: int | None = None,
    year: int | None = None,
) -> list[ColumnElement[Any]]:
    filters: list[ColumnElement[Any]] = []

    if day is not None:
        filters.append(func.extract("day", column) == day)
    if month is not None:
        filters.append(func.extract("month", column) == month)
    if year is not None:
        filters.append(func.extract("year", column) == year)

    return filters


def _transcription_search_filters(
    *,
    client_name: str | None = None,
    case_id: str | None = None,
    subject: str | None = None,
    date_of_recording: datetime.date | None = None,
    date_of_recording_day: int | None = None,
    date_of_recording_month: int | None = None,
    date_of_recording_year: int | None = None,
    client_date_of_birth: datetime.date | None = None,
) -> list[ColumnElement[Any]]:
    filters: list[ColumnElement[Any]] = []

    if client_name:
        filters.append(col(Transcription.client_name).ilike(f"%{client_name}%"))
    if case_id:
        filters.append(col(Transcription.case_id).ilike(f"%{case_id}%"))
    if subject:
        filters.append(col(Transcription.title).ilike(f"%{subject}%"))
    if date_of_recording:
        start = datetime.datetime.combine(date_of_recording, datetime.time.min)
        end = start + datetime.timedelta(days=1)
        created_start = start.replace(tzinfo=datetime.UTC)
        created_end = end.replace(tzinfo=datetime.UTC)
        filters.append(
            or_(
                and_(
                    col(Transcription.date_of_recording).is_not(None),
                    col(Transcription.date_of_recording) >= start,
                    col(Transcription.date_of_recording) < end,
                ),
                and_(
                    col(Transcription.date_of_recording).is_(None),
                    col(Transcription.created_datetime) >= created_start,
                    col(Transcription.created_datetime) < created_end,
                ),
            )
        )
    elif date_of_recording_day or date_of_recording_month or date_of_recording_year:
        date_of_recording_column = cast(ColumnElement[Any], col(Transcription.date_of_recording))
        created_datetime_column = cast(ColumnElement[Any], col(Transcription.created_datetime))
        recorded_date_filters = _date_part_filters(
            date_of_recording_column,
            day=date_of_recording_day,
            month=date_of_recording_month,
            year=date_of_recording_year,
        )
        created_date_filters = _date_part_filters(
            created_datetime_column,
            day=date_of_recording_day,
            month=date_of_recording_month,
            year=date_of_recording_year,
        )
        filters.append(
            or_(
                and_(col(Transcription.date_of_recording).is_not(None), *recorded_date_filters),
                and_(col(Transcription.date_of_recording).is_(None), *created_date_filters),
            )
        )
    if client_date_of_birth:
        start = datetime.datetime.combine(client_date_of_birth, datetime.time.min)
        end = start + datetime.timedelta(days=1)
        filters.append(col(Transcription.client_date_of_birth) >= start)
        filters.append(col(Transcription.client_date_of_birth) < end)

    return filters
