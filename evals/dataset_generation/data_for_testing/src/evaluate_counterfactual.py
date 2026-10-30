import argparse
import asyncio
import json
import logging
from pathlib import Path

from common.llm.client import FastOrBestLLM, create_default_chatbot
from evals.dataset_generation.characteristics.src.transcript_loader import load_transcript
from evals.dataset_generation.data_for_testing.src.counterfactual_evaluator import (
    AxisTransformation,
    evaluate_counterfactual,
)
from evals.dataset_generation.data_for_testing.src.run_helpers import get_transcript_file, load_json
from evals.dataset_generation.data_for_testing.src.settings import INPUT_DIR, OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def _load_dialogue_entries(transcript_file_path: str | Path) -> list[dict]:
    raw = load_json(transcript_file_path)
    if isinstance(raw, dict):
        if "dialogue_entries" not in raw:
            msg = f"Expected 'dialogue_entries' key in {transcript_file_path}"
            raise ValueError(msg)
        entries = raw["dialogue_entries"]
    else:
        entries = raw
    return list(entries)


def _load_axes(input_subdir: Path) -> list[AxisTransformation]:
    axes_file = input_subdir / "axes.json"
    if not axes_file.exists():
        msg = f"axes.json not found in {input_subdir}. Create it to define the counterfactual test axes."
        raise FileNotFoundError(msg)
    with axes_file.open(encoding="utf-8") as f:
        data = json.load(f)
    return [AxisTransformation(**entry) for entry in data]


def _slugify(text: str) -> str:
    return text.lower().replace(" ", "_").replace("/", "_")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Name of the instance to evaluate (matches input/<name> and output/<name>)")
    parser.add_argument("--num-rewrites", type=int, default=2, help="Number of rewrite attempts per axis")
    parser.add_argument("--model", choices=["fast", "best"], default="best", help="LLM tier to use (default: best)")
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

    axes = _load_axes(INPUT_DIR / args.name)
    logging.info("Loaded %d axes from axes.json", len(axes))

    chatbot = create_default_chatbot(FastOrBestLLM[args.model.upper()])
    report = asyncio.run(
        evaluate_counterfactual(reference, dialogue_entries, chatbot, axes=axes, num_rewrites=args.num_rewrites)
    )

    for axis_result in report["axes"]:
        axis_slug = _slugify(axis_result["axis_change"]["axis"])
        target_slug = _slugify(axis_result["axis_change"]["target_value"])
        for rewrite in axis_result["rewrites"]:
            i = rewrite["rewrite_index"]
            rewrite_path = rewrites_dir / f"{axis_slug}_{target_slug}_{i}.txt"
            rewrite_path.write_text(rewrite.pop("transcript"), encoding="utf-8")
            rewrite["transcript_file"] = f"rewrites/{rewrite_path.name}"
            logging.info("Written rewrite %s attempt %d → %s", axis_slug, i, rewrite_path)

    report_path = output_dir / "counterfactual_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logging.info("Written counterfactual report → %s", report_path)

    logging.info("=== COUNTERFACTUAL EVALUATE COMPLETE ===")
