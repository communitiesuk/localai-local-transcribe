import argparse
import csv
import json
import os
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date
from functools import partial
from pathlib import Path

import dotenv

from reporting.aggregate_analytics.caseload import Caseload, load_caseload
from reporting.aggregate_analytics.database import REPO_ROOT, fetch_event_rows
from reporting.aggregate_analytics.measures import (
    MEASURES,
    Count,
    Measure,
    MonthlyCaseloadMeasure,
    MonthlyMeasure,
    RatioMeasure,
)
from reporting.aggregate_analytics.sources import MonthlyCounts, count_event, monthly_counts

Row = dict[str, object]


@dataclass
class Sources:
    """Data access, injectable so measures can be tested without Plausible or Postgres."""

    count: Callable[[Count, str, str], int]
    monthly_counts: Callable[..., MonthlyCounts]
    caseload: Caseload | None = field(default=None)


def percentage(numerator: int, denominator: int | None) -> float | None:
    return round(100 * numerator / denominator, 2) if denominator else None


def months_in_range(start: str, end: str) -> list[str]:
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    months = []
    year, month = first.year, first.month
    while (year, month) <= (last.year, last.month):
        months.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)  # noqa: PLR2004
    return months


def run_ratio(measure: RatioMeasure, start: str, end: str, sources: Sources) -> list[Row]:
    numerator = sources.count(measure.numerator, start, end)
    denominator = sources.count(measure.denominator, start, end)
    return [
        {
            f"numerator ({measure.numerator.label})": numerator,
            f"denominator ({measure.denominator.label})": denominator,
            "percentage": percentage(numerator, denominator),
        }
    ]


def run_monthly(measure: MonthlyMeasure, start: str, end: str, sources: Sources) -> list[Row]:
    counts = sources.monthly_counts(measure.source, measure.events, start, end, by_organisation=False)
    return [{"month": month, "count": counts.get((None, month), 0)} for month in months_in_range(start, end)]


def run_monthly_caseload(measure: MonthlyCaseloadMeasure, start: str, end: str, sources: Sources) -> list[Row]:
    counts = sources.monthly_counts(measure.source, measure.events, start, end, by_organisation=True)
    months = set(months_in_range(start, end))
    caseload = sources.caseload or {}
    # Organisations with a caseload estimate but no events still get a row.
    keys = set(counts) | {key for key in caseload if key[1] in months}

    rows: list[Row] = []
    for organisation_id, month in sorted(keys, key=lambda key: (key[1], key[0] or "")):
        count = counts.get((organisation_id, month), 0)
        estimated = caseload.get((organisation_id, month)) if organisation_id else None
        rows.append(
            {
                "organisation_id": organisation_id,
                "month": month,
                "count": count,
                "estimated_caseload": estimated,
                "percentage": percentage(count, estimated),
            }
        )
    return rows


def run_measure(measure: Measure, start: str, end: str, sources: Sources) -> dict[str, object]:
    if isinstance(measure, RatioMeasure):
        rows = run_ratio(measure, start, end, sources)
    elif isinstance(measure, MonthlyMeasure):
        rows = run_monthly(measure, start, end, sources)
    else:
        rows = run_monthly_caseload(measure, start, end, sources)
    return {"measure": measure.name, "rows": rows}


def run_all(start: str, end: str, sources: Sources) -> list[dict[str, object]]:
    return [run_measure(measure, start, end, sources) for measure in MEASURES]


OUTPUT_DIR = Path(__file__).parent / "output"


def report_folder_name(start: str, end: str) -> str:
    """Folder name for a reporting period's output files, e.g. '2026-09-01_to_2026-09-30'."""
    return f"{start}_to_{end}"


def write_report(report: list[dict[str, object]], filename: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """Write the report as JSON into output_dir, creating it if needed."""
    if Path(filename).name != filename:
        msg = "filename must be a file name, not a path; it is written inside the output directory"
        raise ValueError(msg)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(json.dumps(report, indent=2) + "\n")
    return path


def slugify(name: str) -> str:
    """Turn a measure name into a safe, lowercase, underscore-separated file name stem."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def write_csv_reports(report: list[dict[str, object]], output_dir: Path = OUTPUT_DIR) -> list[Path]:
    """Write one CSV file per measure into output_dir, creating it if needed.

    Each measure's rows share one set of columns (e.g. ratio measures have numerator/denominator/percentage,
    monthly measures have month/count), so they are written as separate files rather than one combined CSV.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for entry in report:
        rows: list[Row] = entry["rows"]  # type: ignore[assignment]
        path = output_dir / f"{slugify(str(entry['measure']))}.csv"
        with path.open("w", newline="") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
        paths.append(path)
    return paths


ENV_FILES = (Path(__file__).parent / ".env", REPO_ROOT / ".env")


ENV_PREFIXES = ("PLAUSIBLE_",)


def load_env(paths: Iterable[Path] = ENV_FILES, prefixes: tuple[str, ...] = ENV_PREFIXES) -> None:
    """Load matching variables from .env files without overriding anything already set.

    Exported variables win, then earlier files. Only the tool's own prefixes are taken so the root .env's local
    AWS_* placeholders can't override an SSO login.
    """
    for path in paths:
        for name, value in dotenv.dotenv_values(path).items():
            if value is not None and name.startswith(prefixes):
                os.environ.setdefault(name, value)


REQUIRED_ENV = ("PLAUSIBLE_BASE_URL", "PLAUSIBLE_SITE_ID", "PLAUSIBLE_API_KEY")


def missing_env(names: Iterable[str] = REQUIRED_ENV) -> list[str]:
    return [name for name in names if not os.environ.get(name)]


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Aggregate Plausible and in-house analytics measures.")
    parser.add_argument("--start", required=True, type=date.fromisoformat, help="Inclusive start date, YYYY-MM-DD")
    parser.add_argument("--end", required=True, type=date.fromisoformat, help="Inclusive end date, YYYY-MM-DD")
    parser.add_argument(
        "--caseload",
        type=Path,
        help="CSV of estimated caseload (organisation_id, month, estimated_caseload); needed for measures 6 and 7",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        help="Write the report into reporting/aggregate_analytics/output/<start>_to_<end>/ (created if missing) "
        "instead of stdout: 'json' writes a single report.json, 'csv' writes one <measure>.csv file per measure",
    )
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must not be before --start")
    if missing := missing_env():
        parser.error(
            f"missing environment variables: {', '.join(missing)}. "
            "Set them in the shell or reporting/aggregate_analytics/.env (see README)"
        )

    caseload = load_caseload(args.caseload) if args.caseload else None
    if caseload is None:
        sys.stderr.write("No --caseload given: estimated caseload and percentages will be null for measures 6 and 7.\n")

    start, end = args.start.isoformat(), args.end.isoformat()
    rows = fetch_event_rows(args.start, args.end)
    sources = Sources(
        count=partial(count_event, rows),
        monthly_counts=partial(monthly_counts, rows),
        caseload=caseload,
    )

    report = run_all(start, end, sources)
    if args.format == "json":
        run_dir = OUTPUT_DIR / report_folder_name(start, end)
        sys.stderr.write(f"Report written to {write_report(report, 'report.json', run_dir)}\n")
    elif args.format == "csv":
        run_dir = OUTPUT_DIR / report_folder_name(start, end)
        paths = write_csv_reports(report, run_dir)
        sys.stderr.write(f"Report written to {len(paths)} file(s) in {run_dir}\n")
    else:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
