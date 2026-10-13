from pathlib import Path
from unittest.mock import MagicMock

import pytest

from reporting.aggregate_analytics import database
from reporting.aggregate_analytics.database import (
    EventRow,
    count_rows,
    fetch_event_rows,
    monthly_count_rows,
    parse_event_rows,
)

ORG_A = "11111111-1111-1111-1111-111111111111"

CSV_TEXT = (
    "event_type,recording_source,organisation_id,month,event_count\n"
    f"SUMMARY_RECEIVED,,{ORG_A.upper()},2026-09,10\n"
    f"TRANSCRIPTION_RECEIVED,live_recording,{ORG_A},2026-09,7\n"
    "TRANSCRIPTION_RECEIVED,direct_upload,,2026-10,3\n"
)


def test_parse_event_rows_normalises_blanks_and_case() -> None:
    assert parse_event_rows(CSV_TEXT) == [
        EventRow("SUMMARY_RECEIVED", None, ORG_A, "2026-09", 10),
        EventRow("TRANSCRIPTION_RECEIVED", "live_recording", ORG_A, "2026-09", 7),
        EventRow("TRANSCRIPTION_RECEIVED", "direct_upload", None, "2026-10", 3),
    ]


def test_count_rows_filters_by_event_and_recording_source() -> None:
    rows = parse_event_rows(CSV_TEXT)

    assert count_rows(rows, "TRANSCRIPTION_RECEIVED") == 10
    assert count_rows(rows, "TRANSCRIPTION_RECEIVED", "live_recording") == 7
    assert count_rows(rows, "SUMMARY_RECEIVED") == 10


def test_monthly_count_rows_groups_by_month_and_optionally_organisation() -> None:
    rows = parse_event_rows(CSV_TEXT)

    assert monthly_count_rows(rows, ("TRANSCRIPTION_RECEIVED",), by_organisation=False) == {
        (None, "2026-09"): 7,
        (None, "2026-10"): 3,
    }
    assert monthly_count_rows(rows, ("TRANSCRIPTION_RECEIVED",), by_organisation=True) == {
        (ORG_A, "2026-09"): 7,
        (None, "2026-10"): 3,
    }


def _fake_run(monkeypatch: pytest.MonkeyPatch, returncode: int = 0) -> MagicMock:
    def run(command: list[str], **kwargs: object) -> MagicMock:
        if command[0] == "aws":
            return MagicMock(returncode=0, stdout="", stderr="")
        output_path = Path(command[command.index("-o") + 1])
        output_path.write_text(CSV_TEXT)
        kwargs["stdout"].write("boom\n")  # type: ignore[attr-defined]
        return MagicMock(returncode=returncode)

    mock = MagicMock(side_effect=run)
    monkeypatch.setattr(database.subprocess, "run", mock)
    return mock


def test_local_environment_runs_psql_directly(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_DB", "POSTGRES_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    run = _fake_run(monkeypatch)

    rows = fetch_event_rows("local", "2026-09-01", "2026-09-30")

    command = run.call_args.args[0]
    assert command[0] == "psql"
    assert "start=2026-09-01" in command
    assert "end=2026-09-30" in command
    assert run.call_args.kwargs["env"]["PGHOST"] == "localhost"
    assert len(rows) == 3


def test_local_environment_maps_backend_postgres_variables_to_psql(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "db.internal")
    monkeypatch.setenv("POSTGRES_PORT", "6543")
    monkeypatch.setenv("POSTGRES_USER", "reporter")
    monkeypatch.setenv("POSTGRES_DB", "other_db")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    run = _fake_run(monkeypatch)

    fetch_event_rows("local", "2026-09-01", "2026-09-30")

    env = run.call_args.kwargs["env"]
    assert (env["PGHOST"], env["PGPORT"], env["PGUSER"], env["PGDATABASE"], env["PGPASSWORD"]) == (
        "db.internal",
        "6543",
        "reporter",
        "other_db",
        "secret",
    )


def test_aws_environment_goes_through_the_tunnel_script(monkeypatch: pytest.MonkeyPatch) -> None:
    run = _fake_run(monkeypatch)

    fetch_event_rows("development", "2026-09-01", "2026-09-30")

    command = run.call_args.args[0]
    assert command[0] == "bash"
    assert Path(command[1]).name == "connect-to-aws-db.sh"
    assert command[2:4] == ["--environment", "development"]
    assert command[4] == "--"
    assert "--csv" in command[5:]


def test_patched_script_defaults_missing_database_name_and_leaves_original_alone(tmp_path: Path) -> None:
    original = database.CONNECT_SCRIPT.read_text()

    patched = database.patched_connect_script(tmp_path)

    text = patched.read_text()
    assert patched != database.CONNECT_SCRIPT
    assert text.index('DB_NAME="postgres"') < text.index('DB_USER="postgres"')
    assert text.replace(database.DB_NAME_FALLBACK, "") == original
    assert database.CONNECT_SCRIPT.read_text() == original


def test_patched_script_falls_back_to_original_when_anchor_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    other = tmp_path / "other.sh"
    other.write_text("echo no anchor here\n")
    monkeypatch.setattr(database, "CONNECT_SCRIPT", other)

    assert database.patched_connect_script(tmp_path / "out") == other


def test_query_failure_raises_with_output(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_run(monkeypatch, returncode=2)

    with pytest.raises(RuntimeError, match="boom"):
        fetch_event_rows("local", "2026-09-01", "2026-09-30")
