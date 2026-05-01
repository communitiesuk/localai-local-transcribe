import logging
from pathlib import Path

from evals.dataset_generation.data_for_testing.src.evaluator import (
    evaluate_manual_vs_hypothesis,
    semantic_similarity,
)
from evals.dataset_generation.data_for_testing.src.run_helpers import load_json, load_json_list, write_results
from evals.dataset_generation.data_for_testing.src.settings import DATA_TEST_TRANSCRIPTS_DIR, OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

if __name__ == "__main__":
    logging.info("=== STARTING EVALUATE ===")

    manifest_path = DATA_TEST_TRANSCRIPTS_DIR / "manifest.json"
    manifest = load_json(manifest_path)
    auto_pc_file_path = Path(manifest["characteristics_output_file"])
    manual_file_path = Path(manifest["manual_file"])

    auto_pcs = load_json(auto_pc_file_path)
    manual_list = load_json_list(manual_file_path)

    if auto_pcs.get("detected_characteristics"):
        results = evaluate_manual_vs_hypothesis(
            manual_list=manual_list, auto_pcs=auto_pcs, text_similarity=semantic_similarity
        )
        write_results(results, OUTPUT_DIR)
    else:
        logging.error("Invalid or empty detected_characteristics in file: %s", auto_pc_file_path)

    logging.info("=== EVALUATE COMPLETE ===")
