import argparse
import asyncio
import json
import logging
from pathlib import Path

from common.llm.client import FastOrBestLLM, create_default_chatbot
from evals.dataset_generation.characteristics.src.transcript_loader import load_transcript
from evals.dataset_generation.data_for_testing.src.counterfactual_evaluator import evaluate_counterfactual
from evals.dataset_generation.data_for_testing.src.run_helpers import get_transcript_file, load_json
from evals.dataset_generation.data_for_testing.src.settings import INPUT_DIR, OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def _load_dialogue_entries(transcript_file_path: str | Path) -> list[dict]:
    raw = load_json(transcript_file_path)
    entries = raw.get("dialogue_entries", raw) if isinstance(raw, dict) else raw
    return list(entries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Name of the instance to evaluate (matches input/<name> and output/<name>)")
    parser.add_argument("--num-alternatives", type=int, default=2, help="Number of counterfactual axes to propose")
    args = parser.parse_args()

    logging.info("=== STARTING COUNTERFACTUAL EVALUATE ===")

    output_dir = OUTPUT_DIR / args.name
    rewrites_dir = output_dir / "rewrites"
    rewrites_dir.mkdir(parents=True, exist_ok=True)

    reference = load_json(output_dir / "reference.json")

    transcript_file = get_transcript_file(INPUT_DIR / args.name)
    transcript_text = load_transcript(transcript_file)
    dialogue_entries = _load_dialogue_entries(transcript_file)

    original_path = rewrites_dir / "original.txt"
    original_path.write_text(transcript_text, encoding="utf-8")
    logging.info("Written original transcript → %s", original_path)

    chatbot = create_default_chatbot(FastOrBestLLM.FAST)
    report = asyncio.run(evaluate_counterfactual(reference, dialogue_entries, chatbot, args.num_alternatives))

    for rewrite in report["rewrites"]:
        i = rewrite["alternative_index"]
        rewrite_path = rewrites_dir / f"rewrite_{i}.txt"
        rewrite_path.write_text(rewrite.pop("transcript"), encoding="utf-8")
        rewrite["transcript_file"] = f"rewrites/rewrite_{i}.txt"
        logging.info("Written rewrite %d → %s", i, rewrite_path)

    report_path = output_dir / "counterfactual_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logging.info("Written counterfactual report → %s", report_path)

    logging.info("=== COUNTERFACTUAL EVALUATE COMPLETE ===")
