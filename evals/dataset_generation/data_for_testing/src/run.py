import logging
import shutil
import subprocess
from pathlib import Path

from evals.dataset_generation.data_for_testing.src.run_helpers import (
    export_results,
    extract_dialogue_entries,
    run_characteristics_pipeline,
    validate_json,
)

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


logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


# def run_command() -> None:
#     logging.info("Running transcription generation...")
#     subprocess.run(COMMAND, check=True)
#     logging.info("Command completed successfully.")


def run_command() -> None:
    logging.info("Running transcription generation...")

    result = subprocess.run(COMMAND, capture_output=True, text=True, check=False)  # noqa: S603

    if result.returncode != 0:
        logging.error("Command failed with exit code %s", result.returncode)
        logging.error("STDOUT:\n%s", result.stdout)
        logging.error("STDERR:\n%s", result.stderr)
        error_msg = f"Transcription generation failed with exit code {result.returncode}"
        raise RuntimeError(error_msg)

    logging.info("Command completed successfully.")


def get_latest_json_file() -> Path:
    files = list(TRANSCRIPTION_GEN_OUTPUT_DIR.glob("*.json"))

    if not files:
        error_msg = f"No JSON files found in {TRANSCRIPTION_GEN_OUTPUT_DIR}"
        raise FileNotFoundError(error_msg)

    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    logging.info("Latest output file detected: %s", latest_file)

    return latest_file


def clear_target_dir() -> None:
    """Clears all contents of TARGET_DIR safely as the
    Characteristic module expects one file within the input dir.
    """

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    existing = list(TARGET_DIR.iterdir())

    if not existing:
        logging.info("Target directory already empty: %s", TARGET_DIR)
        return

    # Safeguard
    min_path_depth = 3
    if len(TARGET_DIR.parts) < min_path_depth:
        error_msg = f"Refusing to clear directory with insufficient path depth: {TARGET_DIR}"
        raise ValueError(error_msg)

    for item in existing:
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
                logging.info("Deleted file: %s", item)
            elif item.is_dir():
                shutil.rmtree(item)
                logging.info("Deleted directory: %s", item)
        except (OSError, PermissionError) as e:
            logging.error("Failed to delete %s: %s", item, e)

    logging.info("Cleared target directory: %s", TARGET_DIR)


def copy_file(src: Path) -> None:
    dest = TARGET_DIR / f"{src.stem}_dialogue_entries.json"

    if dest.exists():
        logging.warning("Overwriting existing file: %s", dest)

    if src.suffix.lower() != ".json":
        error_msg = f"Refusing to copy non-JSON file: {src.name}"
        raise ValueError(error_msg)

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
