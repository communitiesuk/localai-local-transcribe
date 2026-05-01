import json
import logging
import shutil
from pathlib import Path

from evals.dataset_generation.characteristics.src.chunker import find_spans
from evals.dataset_generation.characteristics.src.transcript_loader import load_transcript
from evals.dataset_generation.data_for_testing.src.run_helpers import (
    export_results,
    extract_dialogue_entries,
    load_json_list,
    run_characteristics_pipeline,
    validate_json,
)
from evals.dataset_generation.data_for_testing.src.settings import (
    CHARACTERISTICS_INPUT_DIR,
    DATA_TEST_TRANSCRIPTS_DIR,
    INPUT_DIR,
)

TARGET_DIR = CHARACTERISTICS_INPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def get_input_subdir() -> Path:
    dirs = [d for d in INPUT_DIR.iterdir() if d.is_dir()]
    if not dirs:
        error_msg = f"No input subdirectories found in {INPUT_DIR}"
        raise FileNotFoundError(error_msg)
    latest = max(dirs, key=lambda d: d.stat().st_mtime)
    logging.info("Using input directory: %s", latest)
    return latest


def get_transcript_file(subdir: Path) -> Path:
    files = [f for f in subdir.iterdir() if f.is_file() and f.name != "manual_pc.json" and f.suffix == ".json"]
    if not files:
        error_msg = f"No transcript JSON found in {subdir}"
        raise FileNotFoundError(error_msg)
    return max(files, key=lambda f: f.stat().st_mtime)


def create_annotated_output(manual_list: list[str], transcript_text: str) -> dict:
    """Converts manual_pc.json text spans into characteristics-format JSON with aligned span indices.

    Uses the same transcript string and span search pattern as the characteristics detection
    pipeline (load_transcript + re.escape/finditer), so indices are directly comparable.
    """
    evidence_spans = []
    for text in manual_list:
        for start, end in find_spans(text, transcript_text):
            evidence_spans.append({"text": text, "start_index": start, "end_index": end})

    return {
        "version": "1.0",
        "detected_characteristics": [
            {
                "characteristic": "manual_annotation",
                "attribute_value": "manually identified",
                "evidence_spans": evidence_spans,
            }
        ],
    }


def clear_target_dir() -> None:
    """Clears all contents of TARGET_DIR safely as the
    Characteristic module expects one file within the input dir.
    """
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    existing = list(TARGET_DIR.iterdir())

    if not existing:
        logging.info("Target directory already empty: %s", TARGET_DIR)
        return

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
    logging.info("=== ANNOTATE START ===")

    subdir = get_input_subdir()
    manual_pc_path = subdir / "manual_pc.json"

    if not manual_pc_path.exists():
        error_msg = f"manual_pc.json not found in {subdir}"
        raise FileNotFoundError(error_msg)

    transcript = get_transcript_file(subdir)
    validate_json(transcript)

    manual_list = load_json_list(manual_pc_path)
    transcript_text = load_transcript(transcript)

    annotated = create_annotated_output(manual_list, transcript_text)
    annotated_path = DATA_TEST_TRANSCRIPTS_DIR / f"annotated_{transcript.stem}.json"
    with annotated_path.open("w", encoding="utf-8") as f:
        json.dump(annotated, f, indent=2)
    logging.info("Written annotated output → %s", annotated_path)

    clear_target_dir()
    copy_file(transcript)
    run_characteristics_pipeline()
    export_results(manual_pc_path, annotated_path)

    logging.info("=== ANNOTATE COMPLETE - run evaluate next ===")


if __name__ == "__main__":
    main()
