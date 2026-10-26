import csv
from pathlib import Path

from reporting.analytics_events.database import ANALYTICS_EVENTS_QUERY, ORGANISATIONS_QUERY, fetch_rows

OUTPUT_DIR = Path(__file__).parent / "output"


def write_csv(rows: list[dict[str, object]], filename: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """Write rows as a CSV with a header row, using the first row's keys as the column order."""
    if not rows:
        msg = f"no rows returned for {filename}"
        raise ValueError(msg)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> None:
    write_csv(fetch_rows(ANALYTICS_EVENTS_QUERY), "analytics_events.csv")
    write_csv(fetch_rows(ORGANISATIONS_QUERY), "organisations.csv")


if __name__ == "__main__":
    main()
