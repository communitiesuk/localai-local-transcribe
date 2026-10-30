import argparse
import json
import logging

from evals.dataset_generation.data_for_testing.src.evaluator import evaluate_by_index
from evals.dataset_generation.data_for_testing.src.run_helpers import (
    copy_characteristics_output,
    get_transcript_file,
    load_json,
    run_characteristics_pipeline,
)
from evals.dataset_generation.data_for_testing.src.settings import INPUT_DIR, OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Name of the instance to evaluate (matches input/<name> and output/<name>)")
    args = parser.parse_args()

    logger.info("=== STARTING EVALUATE ===")

    output_dir = OUTPUT_DIR / args.name
    reference = load_json(output_dir / "reference.json")

    transcript = get_transcript_file(INPUT_DIR / args.name)
    output_stem = run_characteristics_pipeline(transcript)

    hypothesis_path = copy_characteristics_output(output_dir, output_stem)
    hypothesis = load_json(hypothesis_path)
    logger.info("Saved hypothesis → %s", hypothesis_path)

    if hypothesis.get("detected_characteristics"):
        metrics = evaluate_by_index(reference, hypothesis)
        metrics_path = output_dir / "metrics.json"
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        logger.info("Written metrics → %s", metrics_path)
    else:
        logger.error("Empty detected_characteristics in hypothesis output")

    logger.info("=== EVALUATE COMPLETE ===")
