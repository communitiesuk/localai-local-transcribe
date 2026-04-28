import json
import logging
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evals.dataset_generation.data_for_testing.src.settings import CHARACTERISTICS_OUTPUT_DIR, DATA_TEST_TRANSCRIPTS_DIR

MANUAL_DIR = DATA_TEST_TRANSCRIPTS_DIR / "manual"


def run_characteristics_pipeline() -> None:
    cmd = ["poetry", "run", "python", "-m", "evals.characteristics.src.main"]

    logging.info("Running characteristics pipeline...")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)  # noqa: S603

        logging.info("Pipeline completed successfully")
        logging.debug("STDOUT:\n%s", result.stdout)

    except subprocess.CalledProcessError as e:
        logging.error("Pipeline failed")
        logging.error("STDOUT:\n%s", e.stdout)
        logging.error("STDERR:\n%s", e.stderr)
        raise


def get_latest_file(directory: Path) -> Path:
    files = [f for f in directory.iterdir() if f.is_file()]

    if not files:
        error_msg = f"No files found in {directory}"
        raise ValueError(error_msg)

    return max(files, key=lambda f: f.stat().st_mtime)


def export_results() -> None:
    DATA_TEST_TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    MANUAL_DIR.mkdir(parents=True, exist_ok=True)

    latest_file = get_latest_file(CHARACTERISTICS_OUTPUT_DIR)

    dest_json = DATA_TEST_TRANSCRIPTS_DIR / latest_file.name
    manual_filename = f"manual_pcs_{latest_file.stem}.py"
    manual_file_path = MANUAL_DIR / manual_filename
    manifest_path = DATA_TEST_TRANSCRIPTS_DIR / "manifest.json"

    shutil.copy2(latest_file, dest_json)
    logging.info("Copied output file → %s", dest_json)

    if not manual_file_path.exists():
        manual_file_path.touch()
        logging.info("Created manual file → %s", manual_file_path)
    else:
        logging.info("Manual file already exists → %s", manual_file_path)

    manifest = {
        "source_file": str(latest_file),
        "characteristics_output_file": str(dest_json),
        "manual_file": str(manual_file_path),
    }

    with Path(manifest_path).open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logging.info("Wrote manifest → %s", manifest_path)


def write_results(results: dict[str, Any], output_dir: Path, prefix: str = "evaluation") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    file_path = output_dir / f"{prefix}_{timestamp}.json"

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logging.info("Results written to %s", file_path)

    return file_path


def extract_dialogue_entries(src_path: Path, dest_path: Path) -> None:
    """Extracts dialogue_entries array and writes it as a flat JSON list."""

    with src_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "dialogue_entries" not in data:
        error_msg = f"'dialogue_entries' key not found in {src_path}"
        raise ValueError(error_msg)

    dialogue_entries = data["dialogue_entries"]

    if not isinstance(dialogue_entries, list):
        error_msg = f"'dialogue_entries' is not a list in {src_path}"
        raise ValueError(error_msg)

    # validate shape
    for i, item in enumerate(dialogue_entries):
        if not isinstance(item, dict):
            error_msg = f"Entry {i} in 'dialogue_entries' is not a dict in {src_path}"
            raise ValueError(error_msg)
        if "speaker" not in item or "text" not in item:
            error_msg = f"Entry {i} missing 'speaker' or 'text' keys in {src_path}"
            raise ValueError(error_msg)

    with dest_path.open("w", encoding="utf-8") as f:
        json.dump(dialogue_entries, f, indent=2)

    logging.info("Extracted %d dialogue entries", len(dialogue_entries))
    logging.info("Written to: %s", dest_path)


def validate_json(file_path: Path) -> None:
    try:
        with file_path.open("r", encoding="utf-8") as f:
            json.load(f)
        logging.info("JSON validation passed: %s", file_path.name)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in {file_path}: {e}"
        raise ValueError(error_msg) from e


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        error_msg = f"Expected JSON object at {path}, got {type(data)}"
        raise ValueError(error_msg)

    return data
