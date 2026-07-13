from __future__ import annotations

import json
from pathlib import Path

from evals.summarisation.src.security.security_types import SecurityScenarioInput


def load_security_json(file_path: Path) -> SecurityScenarioInput:
    """Loads and validates a single injection scenario from a JSON file."""
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return SecurityScenarioInput.model_validate(data)


def discover_security_files(input_dir: Path) -> list[Path]:
    """Discovers all JSON scenario files in the input directory (sorted for determinism)."""
    if not input_dir.exists():
        msg = f"Input directory does not exist: {input_dir}"
        raise ValueError(msg)

    json_files = sorted(input_dir.glob("**/*.json"))
    if not json_files:
        msg = f"No JSON files found in {input_dir}"
        raise ValueError(msg)

    return json_files
