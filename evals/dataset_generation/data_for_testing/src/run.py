import subprocess
import argparse
import json
import shutil
from pathlib import Path
import logging

from evals.dataset_generation.data_for_testing.src.run_helpers import (
    run_characteristics_pipeline,
    export_results, 
    extract_dialogue_entries,
    validate_json

)
from datetime import datetime

COMMAND = [
    "poetry",
    "run",
    "python",
    "-m",
    "evals.dataset_generation.transcription_generation.main",
    "--config",
    "multi_with_pcs.yaml",
]

TRANSCRIPTION_GEN_OUTPUT_DIR = Path("evals/dataset_generation/transcription_generation/output/")
TARGET_DIR = Path("evals/characteristics/input/")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def run_command() -> None:
    logging.info("Running transcription generation...")
    subprocess.run(COMMAND, check=True)
    logging.info("Command completed successfully.")


def get_latest_json_file() -> Path:
    files = list(TRANSCRIPTION_GEN_OUTPUT_DIR.glob("*.json"))

    if not files:
        raise FileNotFoundError(f"No JSON files found in {TRANSCRIPTION_GEN_OUTPUT_DIR}")

    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    logging.info("Latest output file detected: %s", latest_file)

    return latest_file



def clear_target_dir()-> None:
    """Clears all contents of TARGET_DIR safely as the
    Characteristic module expects one file within the input dir.
    """

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    existing = list(TARGET_DIR.iterdir())

    if not existing:
        logging.info("Target directory already empty: %s", TARGET_DIR)
        return

    # Safeguard 
    if len(TARGET_DIR.parts) < 3:
        raise ValueError(f"Refusing to clear suspicious path: {TARGET_DIR}")

    for item in existing:
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
                logging.info("Deleted file: %s", item)
            elif item.is_dir():
                shutil.rmtree(item)
                logging.info("Deleted directory: %s", item)
        except Exception as e:
            logging.error("Failed to delete %s: %s", item, e)

    logging.info("Cleared target directory: %s", TARGET_DIR)


def copy_file(src: Path)-> None:
    dest = TARGET_DIR / f"{src.stem}_dialogue_entries.json"

    if dest.exists():
        logging.warning("Overwriting existing file: %s", dest)

    if src.suffix.lower() != ".json":
        raise ValueError(f"Refusing to copy non-JSON file: {src.name}")

    extract_dialogue_entries(src, dest)



def main() -> None:
    logging.info("=== PIPELINE START (1/2) ===")

    run_command()

    latest_file = get_latest_json_file()

    validate_json(latest_file)

    clear_target_dir()

    copy_file(latest_file)

    run_characteristics_pipeline()

    export_results()


    logging.info("===PIPELINE (1/2) COMPLETE ===")
    logging.info("=== ADD MANUAL PC ENTRIES TO LIST THEN RUN SECOND PIPELINE ===")



if __name__ == "__main__":
    main()