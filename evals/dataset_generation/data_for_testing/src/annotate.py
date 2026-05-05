import argparse
import json
import logging
from collections import defaultdict

from evals.dataset_generation.characteristics.src.chunker import find_spans
from evals.dataset_generation.characteristics.src.transcript_loader import load_transcript
from evals.dataset_generation.data_for_testing.src.run_helpers import (
    get_transcript_file,
    load_manual_pc,
    validate_json,
)
from evals.dataset_generation.data_for_testing.src.settings import INPUT_DIR, OUTPUT_DIR
from evals.dataset_generation.data_for_testing.src.types import ManualEntry

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def create_annotated_output(manual_list: list[ManualEntry], transcript_text: str) -> dict:
    """Converts manual_pc.json entries into characteristics-format JSON with aligned span indices.

    Entries are grouped by (category, value); duplicate texts within a group are deduplicated.
    """
    groups: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    for entry in manual_list:
        groups[(entry["category"], entry["value"])].add(entry["text"])

    detected_characteristics = []
    for (category, value), texts in groups.items():
        seen: set[tuple[int, int]] = set()
        evidence_spans = []
        for text in texts:
            for start, end in find_spans(text, transcript_text):
                if (start, end) not in seen:
                    seen.add((start, end))
                    evidence_spans.append({"text": text, "start_index": start, "end_index": end})
        detected_characteristics.append(
            {
                "characteristic": category,
                "attribute_value": value,
                "evidence_spans": evidence_spans,
            }
        )

    return {
        "version": "1.0",
        "detected_characteristics": detected_characteristics,
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

    manual_list = load_manual_pc(manual_pc_path)
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
