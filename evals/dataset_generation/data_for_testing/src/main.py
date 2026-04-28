
from evals.dataset_generation.data_for_testing.transcripts.manual.manual_pcs_transcript_20260427_083757_dialogue_entries_output import (
    segun_biola_manual_pcs
)

from evals.dataset_generation.data_for_testing.transcripts.manual.manual_pcs_transcript_20260427_140409_dialogue_entries_output import (
    thomas_emily_manual_pcs
)

from evals.dataset_generation.data_for_testing.src.evaluator import (
   evaluate_manual_vs_hypothesis
)

from evals.dataset_generation.data_for_testing.src.run_helpers import (
    write_results,
    load_json
)

from evals.dataset_generation.data_for_testing.src.settings import (
    DATA_TEST_TRANSCRIPTS_DIR,
    OUTPUT_DIR
)

from evals.dataset_generation.data_for_testing.src.evaluator import (
    containment_similarity
)

import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def log_file_error(file: str | Path) -> None:
    logging.error("Invalid or empty detected_characteristics in file: %s", file)



if __name__ == '__main__':
    logging.info("=== STARTING PIPELINE (2/2) ===")

    manifest_path = DATA_TEST_TRANSCRIPTS_DIR / "manifest.json"
    manifest = load_json(manifest_path)
    auto_pc_file_path = Path(manifest["characteristics_output_file"])

    auto_pcs = load_json(auto_pc_file_path)

    if auto_pcs.get("detected_characteristics"):
        results = evaluate_manual_vs_hypothesis(thomas_emily_manual_pcs, auto_pcs, containment_similarity)
        write_results(results, OUTPUT_DIR )
    else:
        log_file_error(auto_pc_file_path)   

    logging.info("=== PIPELINE (2/2) COMPLETE ===")


   
