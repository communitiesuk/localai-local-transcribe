import logging
from pathlib import Path

from evals.dataset_generation.data_for_testing.src.evaluator import (
    evaluate_manual_vs_hypothesis,
    semantic_similarity,
)
from evals.dataset_generation.data_for_testing.src.run_helpers import load_json, write_results
from evals.dataset_generation.data_for_testing.src.settings import DATA_TEST_TRANSCRIPTS_DIR, OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def log_file_error(file: str | Path) -> None:
    logging.error("Invalid or empty detected_characteristics in file: %s", file)


if __name__ == "__main__":
    logging.info("=== STARTING PIPELINE (2/2) ===")

    manifest_path = DATA_TEST_TRANSCRIPTS_DIR / "manifest.json"
    manifest = load_json(manifest_path)
    auto_pc_file_path = Path(manifest["characteristics_output_file"])

    auto_pcs = load_json(auto_pc_file_path)

    if auto_pcs.get("detected_characteristics"):
        results = evaluate_manual_vs_hypothesis(
            manual_list=None, auto_pcs=auto_pcs, text_similarity=semantic_similarity
        )
        write_results(results, OUTPUT_DIR)
    else:
        log_file_error(auto_pc_file_path)

    logging.info("=== PIPELINE (2/2) COMPLETE ===")
