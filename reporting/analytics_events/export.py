import csv
from datetime import UTC, datetime
from pathlib import Path

from reporting.analytics_events.database import ANALYTICS_EVENTS_QUERY, ORGANISATIONS_QUERY, fetch_rows

OUTPUT_DIR = Path(__file__).parent / "output"


def write_csv(columns: list[str], rows: list[dict[str, object]], filename: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """Write rows as a CSV with a header row, in the column order the query returned.

    An empty result writes a header-only file rather than raising. The events query excludes the
    current day, so a database holding only today's events returns nothing - and because the events
    file is written first, raising here would abort the run and produce neither CSV.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> None:
    # Shared between both files so a single run's exports are easy to pair up.
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M")
    for query, name in ((ANALYTICS_EVENTS_QUERY, "analytics_events"), (ORGANISATIONS_QUERY, "organisations")):
        columns, rows = fetch_rows(query)
        # Passed explicitly rather than left to write_csv's default, which binds OUTPUT_DIR at import
        # time and so cannot be redirected by tests.
        write_csv(columns, rows, f"{name}_{timestamp}.csv", OUTPUT_DIR)


if __name__ == "__main__":
    main()
