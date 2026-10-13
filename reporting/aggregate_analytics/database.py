import csv
import io
import os
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONNECT_SCRIPT = REPO_ROOT / "connect-to-aws-db.sh"
QUERY_FILE = Path(__file__).parent / "analytics-event-counts.sql"
QUERY_TIMEOUT_SECONDS = 300

# connect-to-aws-db.sh puts the literal "None" in the connection string when RDS reports no DBName (as on instances
# created without db_name, e.g. production). Patches a temp copy rather than the shared script.
PATCH_ANCHOR = 'DB_USER="postgres"\n'
DB_NAME_FALLBACK = (
    'if [[ -z "$DB_NAME" || "$DB_NAME" == "None" ]]; then DB_NAME="postgres"; fi  # added by reporting tool\n'
)


def patched_connect_script(directory: Path) -> Path:
    """Write a copy of connect-to-aws-db.sh with a default database name, leaving the original untouched."""
    script = CONNECT_SCRIPT.read_text(encoding="utf-8")
    if script.count(PATCH_ANCHOR) != 1:
        # The script was restructured (perhaps fixed upstream): run it as-is rather than guess.
        sys.stderr.write("connect-to-aws-db.sh changed; using it without the database name fallback.\n")
        return CONNECT_SCRIPT
    patched = directory / CONNECT_SCRIPT.name
    patched.write_text(script.replace(PATCH_ANCHOR, DB_NAME_FALLBACK + PATCH_ANCHOR), encoding="utf-8")
    return patched


# The backend's POSTGRES_* names (as in .env), translated to the PG* names psql reads. Defaults mirror the local
# connection in reporting/README.md.
LOCAL_POSTGRES_ENV = {
    "POSTGRES_HOST": ("PGHOST", "localhost"),
    "POSTGRES_PORT": ("PGPORT", "5432"),
    "POSTGRES_USER": ("PGUSER", "postgres"),
    "POSTGRES_DB": ("PGDATABASE", "minute_db"),
    "POSTGRES_PASSWORD": ("PGPASSWORD", "insecure"),
}


@dataclass(frozen=True)
class EventRow:
    event_type: str
    recording_source: str | None
    organisation_id: str | None
    month: str
    count: int


def parse_event_rows(csv_text: str) -> list[EventRow]:
    return [
        EventRow(
            event_type=row["event_type"],
            recording_source=row["recording_source"] or None,
            organisation_id=row["organisation_id"].lower() or None,
            month=row["month"],
            count=int(row["event_count"]),
        )
        for row in csv.DictReader(io.StringIO(csv_text))
    ]


def check_aws_login(env: dict[str, str]) -> None:
    """Run the same check as connect-to-aws-db.sh, but surface AWS's own error, which the script discards."""
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["aws", "sts", "get-caller-identity"],  # noqa: S607
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = (
            f"AWS login check failed (AWS_PROFILE={env.get('AWS_PROFILE')!r}): {result.stderr.strip()}\n"
            "Run `aws sso login --profile <profile> && export AWS_PROFILE=<profile>` in this same shell."
        )
        raise RuntimeError(msg)


def fetch_event_rows(environment: str, start: str, end: str) -> list[EventRow]:
    """Run analytics-event-counts.sql through psql: directly for 'local', else via connect-to-aws-db.sh's tunnel."""
    with tempfile.TemporaryDirectory() as tmp:
        # Write results to a file because the tunnel script also prints progress to stdout.
        output_path = Path(tmp) / "counts.csv"
        psql_args = ["--csv", "-v", f"start={start}", "-v", f"end={end}", "-f", str(QUERY_FILE), "-o", str(output_path)]
        env = os.environ.copy()
        if environment == "local":
            command = ["psql", *psql_args]
            for source_name, (psql_name, default) in LOCAL_POSTGRES_ENV.items():
                env[psql_name] = os.environ.get(source_name, default)
        else:
            check_aws_login(env)
            command = ["bash", str(patched_connect_script(Path(tmp))), "--environment", environment, "--", *psql_args]

        log_path = Path(tmp) / "script.log"
        # Log to a file, not pipes: the tunnel's session-manager-plugin can outlive the script and hold pipes open.
        with log_path.open("w", encoding="utf-8") as log:
            try:
                result = subprocess.run(  # noqa: S603 - fixed argv, no shell
                    command,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=log,
                    text=True,
                    check=False,
                    timeout=QUERY_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as error:
                msg = (
                    f"Database query timed out after {QUERY_TIMEOUT_SECONDS}s ({command[0]}). Check for leftover "
                    f"tunnel processes (pgrep -fl session-manager-plugin):\n{log_path.read_text(encoding='utf-8')}"
                )
                raise RuntimeError(msg) from error
        if result.returncode != 0:
            msg = (
                f"Database query failed ({command[0]}, exit {result.returncode}):\n"
                f"{log_path.read_text(encoding='utf-8')}"
            )
            raise RuntimeError(msg)
        return parse_event_rows(output_path.read_text(encoding="utf-8"))


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
