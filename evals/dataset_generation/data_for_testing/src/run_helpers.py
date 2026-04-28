import subprocess
import logging
from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import Any

from evals.dataset_generation.data_for_testing.src.settings import (
    DATA_TEST_TRANSCRIPTS_DIR,
    CHARACTERISTICS_OUTPUT_DIR
)

MANUAL_DIR = DATA_TEST_TRANSCRIPTS_DIR / "manual"


def run_characteristics_pipeline()-> None:
    cmd = [
        "poetry",
        "run",
        "python",
        "-m",
        "evals.characteristics.src.main"
    ]

    logging.info("Running characteristics pipeline...")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

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
        raise ValueError(f"No files found in {directory}")

    latest = max(files, key=lambda f: f.stat().st_mtime)
    return latest



def export_results()-> None:
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

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logging.info("Wrote manifest → %s", manifest_path)


def write_results(results: dict[str,Any], output_dir: Path, prefix: str = "evaluation") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
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
        raise ValueError("Expected 'dialogue_entries' key in source JSON")

    dialogue_entries = data["dialogue_entries"]

    if not isinstance(dialogue_entries, list):
        raise ValueError("'dialogue_entries' must be a list")

    #validate shape
    for i, item in enumerate(dialogue_entries):
        if not isinstance(item, dict):
            raise ValueError(f"Entry {i} is not a dict")
        if "speaker" not in item or "text" not in item:
            raise ValueError(f"Entry {i} missing required keys")

    with dest_path.open("w", encoding="utf-8") as f:
        json.dump(dialogue_entries, f, indent=2)

    print(f"✅ Extracted {len(dialogue_entries)} dialogue entries")
    print(f"📁 Written to: {dest_path}")

def validate_json(file_path: Path) -> None:
    try:
        with file_path.open("r", encoding="utf-8") as f:
            json.load(f)
        logging.info("JSON validation passed: %s", file_path.name)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object, got {type(data)}")

    return data