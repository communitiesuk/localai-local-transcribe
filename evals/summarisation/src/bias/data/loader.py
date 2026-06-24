from __future__ import annotations

import json
from pathlib import Path

from evals.summarisation.src.bias.bias_types import CounterfactualInput
from evals.summarisation.src.bias.constants import SPC_BASELINE_FILENAME


def load_counterfactual_json(file_path: Path) -> CounterfactualInput:
    """Loads and validates counterfactual input data from JSON file."""
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return CounterfactualInput.model_validate(data)


def discover_counterfactual_files(input_dir: Path) -> list[Path]:
    """Discovers all JSON files in input directory for counterfactual evaluation.

    The SPC baseline file (if present) is excluded — it is configuration, not a
    counterfactual transcript pair.
    """
    if not input_dir.exists():
        msg = f"Input directory does not exist: {input_dir}"
        raise ValueError(msg)

    json_files = [path for path in input_dir.glob("**/*.json") if path.name != SPC_BASELINE_FILENAME]
    if not json_files:
        msg = f"No JSON files found in {input_dir}"
        raise ValueError(msg)

    return json_files
