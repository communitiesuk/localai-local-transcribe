import argparse
import json
import logging

from evals.dataset_generation.characteristics.src.chunker import find_spans
from evals.dataset_generation.characteristics.src.transcript_loader import load_transcript
from evals.dataset_generation.data_for_testing.src.run_helpers import (
    get_transcript_file,
    load_json_list,
    validate_json,
)
from evals.dataset_generation.data_for_testing.src.settings import INPUT_DIR, OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def create_annotated_output(manual_list: list[str], transcript_text: str) -> dict:
    """Converts manual_pc.json text spans into characteristics-format JSON with aligned span indices.

    Uses the same transcript string and span search pattern as the characteristics detection
    pipeline (load_transcript + re.escape/finditer), so indices are directly comparable.
    """
    seen: set[tuple[int, int]] = set()
    evidence_spans = []
    for text in set(manual_list):
        for start, end in find_spans(text, transcript_text):
            if (start, end) not in seen:
                seen.add((start, end))
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Name of the subdirectory under input/ to process")
    args = parser.parse_args()

    logging.info("=== ANNOTATE START ===")

    subdir = INPUT_DIR / args.name
    if not subdir.is_dir():
        error_msg = f"Input directory not found: {subdir}"
        raise FileNotFoundError(error_msg)

    manual_pc_path = subdir / "manual_pc.json"
    if not manual_pc_path.exists():
        error_msg = f"manual_pc.json not found in {subdir}"
        raise FileNotFoundError(error_msg)

    transcript = get_transcript_file(subdir)
    validate_json(transcript)

    manual_list = load_json_list(manual_pc_path)
    transcript_text = load_transcript(transcript)

    output_dir = OUTPUT_DIR / args.name
    output_dir.mkdir(parents=True, exist_ok=True)

    reference = create_annotated_output(manual_list, transcript_text)
    reference_path = output_dir / "reference.json"
    with reference_path.open("w", encoding="utf-8") as f:
        json.dump(reference, f, indent=2)
    logging.info("Written reference → %s", reference_path)

    logging.info("=== ANNOTATE COMPLETE - run evaluate next ===")


if __name__ == "__main__":
    main()
