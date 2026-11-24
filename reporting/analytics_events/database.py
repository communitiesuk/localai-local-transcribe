from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from common.settings import get_settings
from reporting.aggregate_analytics.database import build_engine

ANALYTICS_EVENTS_QUERY = Path(__file__).parent / "analytics-events.sql"
ORGANISATIONS_QUERY = Path(__file__).parent / "organisations.sql"


def fetch_rows(query_file: Path) -> tuple[list[str], list[dict[str, object]]]:
    """Run query_file against the database configured via POSTGRES_* and return (columns, rows).

    Columns come from the result metadata rather than from the first row, so they are known even when
    the query matches nothing and the caller can still write a header.
    """
    engine = build_engine(get_settings())
    try:
        with Session(engine) as session:
            result = session.execute(text(query_file.read_text(encoding="utf-8")))
            columns = list(result.keys())
            return columns, [dict(row) for row in result.mappings()]
    finally:
        engine.dispose()
