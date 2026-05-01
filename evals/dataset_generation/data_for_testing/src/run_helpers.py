import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from evals.dataset_generation.data_for_testing.src.settings import CHARACTERISTICS_OUTPUT_DIR


def get_transcript_file(subdir: Path) -> Path:
    files = [f for f in subdir.iterdir() if f.is_file() and f.name != "manual_pc.json" and f.suffix == ".json"]
    if not files:
        error_msg = f"No transcript JSON found in {subdir}"
        raise FileNotFoundError(error_msg)
    return max(files, key=lambda f: f.stat().st_mtime)


def run_characteristics_pipeline() -> None:
    cmd = ["poetry", "run", "python", "-m", "evals.dataset_generation.characteristics.src.main"]

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


def copy_characteristics_output(output_dir: Path, transcript_stem: str) -> Path:
    expected_path = CHARACTERISTICS_OUTPUT_DIR / f"{transcript_stem}_output.json"
    if not expected_path.exists():
        error_msg = f"Expected characteristics output not found: {expected_path}"
        raise FileNotFoundError(error_msg)
    dest = output_dir / "hypothesis.json"
    shutil.copy2(expected_path, dest)
    logging.info("Copied characteristics output → %s", dest)
    return dest


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


def load_json_list(path: str | Path) -> list[str]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        error_msg = f"Expected JSON array at {path}, got {type(data)}"
        raise ValueError(error_msg)
    return data
