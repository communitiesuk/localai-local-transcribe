import csv
from datetime import datetime
from pathlib import Path

# Keyed by (organisation_id, "YYYY-MM").
Caseload = dict[tuple[str, str], int]

REQUIRED_COLUMNS = {"organisation_id", "month", "estimated_caseload"}


def load_caseload(path: Path) -> Caseload:
    """Load the externally-maintained estimated caseload CSV: organisation_id, month (YYYY-MM), estimated_caseload."""
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            msg = f"Caseload file is missing columns: {', '.join(sorted(missing))}"
            raise ValueError(msg)

        caseload: Caseload = {}
        for line_number, row in enumerate(reader, start=2):
            key = (row["organisation_id"].strip().lower(), row["month"].strip())
            try:
                datetime.strptime(key[1], "%Y-%m")  # noqa: DTZ007 - only validating the format
            except ValueError as e:
                msg = f"Line {line_number}: month must be YYYY-MM, got {key[1]!r}"
                raise ValueError(msg) from e
            if key in caseload:
                msg = f"Line {line_number}: duplicate caseload for organisation {key[0]} in {key[1]}"
                raise ValueError(msg)
            caseload[key] = int(row["estimated_caseload"])
    return caseload
