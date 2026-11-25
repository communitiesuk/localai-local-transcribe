"""Fail if frontend/openapi.json does not match the spec the backend generates.

Run from the repository root with `poetry run python -m scripts.check_openapi_json`.
"""

import json
import sys
from difflib import unified_diff
from pathlib import Path

from backend.main import app

MAX_DIFF_LINES = 60
FIX = "Fix it by running `npm run openapi-ts` in frontend/ against the running backend, then commit the result."

COMMITTED_SPEC = Path(__file__).resolve().parents[1] / "frontend" / "openapi.json"


def as_sorted_lines(spec: object) -> list[str]:
    return json.dumps(spec, indent=2, sort_keys=True).splitlines()


if not COMMITTED_SPEC.is_file():
    sys.exit(f"{COMMITTED_SPEC} does not exist. {FIX}")

committed = json.loads(COMMITTED_SPEC.read_text(encoding="utf-8"))
generated = app.openapi()

if committed == generated:
    # print rather than a log since this is a script and the output belongs in stdout
    print("frontend/openapi.json matches the backend.")  # noqa: T201
    sys.exit(0)

# The committed file is prettier formatted and the generated one is not, so both sides are
# re-serialised before diffing to keep the output to the real differences.
difference = list(
    unified_diff(
        as_sorted_lines(committed),
        as_sorted_lines(generated),
        fromfile="frontend/openapi.json",
        tofile="generated from the backend",
        lineterm="",
    )
)
shown = difference[:MAX_DIFF_LINES]
if len(difference) > MAX_DIFF_LINES:
    shown.append(f"... and {len(difference) - MAX_DIFF_LINES} more lines of difference")

sys.exit("\n".join(["frontend/openapi.json is out of date with the backend.", FIX, "", *shown]))
