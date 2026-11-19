import csv
from pathlib import Path
from unittest.mock import MagicMock, patch

from reporting.analytics_events.database import fetch_rows
from reporting.analytics_events.export import main, write_csv

COLUMNS = ["id", "occurred_datetime", "event_metadata"]
ROWS: list[dict[str, object]] = [
    {"id": "a", "occurred_datetime": "2026-11-16 09:00:00", "event_metadata": '{"edit_type": "x"}'},
    {"id": "b", "occurred_datetime": "2026-11-16 10:00:00", "event_metadata": ""},
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def test_write_csv_writes_header_and_rows(tmp_path: Path) -> None:
    path = write_csv(COLUMNS, ROWS, "events.csv", output_dir=tmp_path)

    columns, rows = read_csv(path)
    assert columns == COLUMNS
    assert len(rows) == 2
    assert rows[0]["event_metadata"] == '{"edit_type": "x"}'


# The events query excludes the current day, so a database holding only today's events returns
# nothing. The events file is written first, so raising here would abort the run before the
# organisations file was written and leave the operator with no output at all.
def test_write_csv_writes_a_header_only_file_when_there_are_no_rows(tmp_path: Path) -> None:
    path = write_csv(COLUMNS, [], "events.csv", output_dir=tmp_path)

    columns, rows = read_csv(path)
    assert columns == COLUMNS
    assert rows == []


def test_main_writes_both_files_when_the_events_query_returns_nothing(tmp_path: Path) -> None:
    organisations = ([*COLUMNS], [dict(ROWS[0])])
    with (
        patch("reporting.analytics_events.export.OUTPUT_DIR", tmp_path),
        patch(
            "reporting.analytics_events.export.fetch_rows",
            side_effect=[(COLUMNS, []), organisations],
        ),
    ):
        main()

    events = list(tmp_path.glob("analytics_events_*.csv"))
    orgs = list(tmp_path.glob("organisations_*.csv"))
    assert len(events) == 1
    assert len(orgs) == 1
    assert read_csv(events[0]) == (COLUMNS, [])
    assert len(read_csv(orgs[0])[1]) == 1


def test_fetch_rows_takes_columns_from_result_metadata_not_the_first_row(tmp_path: Path) -> None:
    """An empty result still has to yield column names, which rows[0].keys() cannot provide."""
    query_file = tmp_path / "query.sql"
    query_file.write_text("SELECT 1;", encoding="utf-8")

    result = MagicMock()
    result.keys.return_value = COLUMNS
    result.mappings.return_value = []
    session = MagicMock()
    session.execute.return_value = result

    with (
        patch("reporting.analytics_events.database.build_engine"),
        patch("reporting.analytics_events.database.get_settings"),
        patch("reporting.analytics_events.database.Session") as session_cls,
    ):
        session_cls.return_value.__enter__.return_value = session
        columns, rows = fetch_rows(query_file)

    assert columns == COLUMNS
    assert rows == []
