import argparse
import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import yaml

from evals.dataset_generation.counterfactual_generation.src.config import CounterfactualConfig
from evals.dataset_generation.counterfactual_generation.src.models import (
    AxisChange,
    CharacteristicDetection,
    CounterfactualOutput,
    EvidenceSpan,
    TranscriptInput,
)
from evals.dataset_generation.counterfactual_generation.src.rewriter import CounterfactualRewriter
from evals.dataset_generation.counterfactual_generation.src.visualizer import generate_modification_report
from evals.dataset_generation.shared_constants import ProtectedCharacteristic

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

WORKDIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = WORKDIR.parent.parent.parent


def _convert_characteristics_schema(char_data: dict, dialogue_entries: list) -> CharacteristicDetection:
    """Convert characteristics detection schema to counterfactual schema.

    Maps character-level spans to dialogue entry indices by reconstructing the transcript
    in the same format as the characteristic detection (speaker: text with newlines).
    """
    dialogue_positions = []
    current_pos = 0
    for idx, entry in enumerate(dialogue_entries):
        entry_text = f"{entry['speaker']}: {entry['text']}"
        entry_length = len(entry_text)
        dialogue_positions.append((current_pos, current_pos + entry_length, idx))
        current_pos += entry_length + 1

    evidence_spans = []
    for span in char_data.get("evidence_spans", []):
        start_idx = span.get("start_index")
        end_idx = span.get("end_index")
        text = span.get("text", "")

        if start_idx is None or end_idx is None:
            continue

        dialogue_idx = None
        for start_pos, end_pos, idx in dialogue_positions:
            if start_pos <= start_idx < end_pos:
                dialogue_idx = idx
                break

        if dialogue_idx is not None:
            evidence_spans.append(
                EvidenceSpan(
                    dialogue_index=dialogue_idx,
                    text_snippet=text,
                    confidence=1.0,
                )
            )

    return CharacteristicDetection(
        axis=char_data["characteristic"],
        detected_value=char_data["attribute_value"],
        evidence_spans=evidence_spans,
        overall_confidence=1.0,
    )


def _load_characteristic_detections(
    detection_path: Path, dialogue_entries: list
) -> dict[ProtectedCharacteristic, CharacteristicDetection]:
    """Load all characteristic detections from file, returning a dict keyed by axis."""
    logger.info("Loading characteristic detection from: %s", detection_path)
    with detection_path.open() as f:
        detection_data = json.load(f)

    detections_by_axis = {}

    if "detected_characteristics" in detection_data:
        detected_chars = detection_data["detected_characteristics"]
        if detected_chars:
            logger.info("Found %d detected characteristics", len(detected_chars))
            for char_data in detected_chars:
                detection = _convert_characteristics_schema(char_data, dialogue_entries)
                detections_by_axis[detection.axis] = detection
        else:
            logger.warning("No characteristics detected in file, will use config-based axes")
    else:
        detection = CharacteristicDetection(**detection_data)
        detections_by_axis[detection.axis] = detection

    return detections_by_axis


async def generate_counterfactual_from_config(config: CounterfactualConfig) -> list[CounterfactualOutput]:
    transcript_path = config.get_transcript_path(PROJECT_ROOT)

    logger.info("Loading transcript from: %s", transcript_path)
    with transcript_path.open() as f:
        transcript_data = json.load(f)

    if isinstance(transcript_data, dict) and "dialogue_entries" in transcript_data:
        dialogue_entries = transcript_data["dialogue_entries"]
    elif isinstance(transcript_data, list):
        dialogue_entries = transcript_data
    else:
        dialogue_entries = transcript_data.get("dialogue_entries", transcript_data)

    if not dialogue_entries:
        msg = f"No dialogue_entries found in transcript file: {transcript_path}"
        raise ValueError(msg)

    transcript_input = TranscriptInput(dialogue_entries=dialogue_entries)

    characteristic_detection_path = config.get_characteristic_detection_path(PROJECT_ROOT)
    if characteristic_detection_path:
        detections_by_axis = _load_characteristic_detections(characteristic_detection_path, dialogue_entries)
    else:
        logger.info("No characteristic detection file provided, using config-based axes")
        detections_by_axis = {}

    run_timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    run_output_dir = WORKDIR / "output" / f"run_{run_timestamp}"
    run_output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    rewriter = CounterfactualRewriter()

    for axis_def in config.axes:
        logger.info("Processing axis: %s (%s -> %s)", axis_def.axis, axis_def.original_value, axis_def.target_value)

        axis_change = AxisChange(
            axis=axis_def.axis,
            original_value=axis_def.original_value,
            target_value=axis_def.target_value,
            instructions=axis_def.instructions,
        )

        if detections_by_axis:
            if axis_change.axis in detections_by_axis:
                detection_to_use = detections_by_axis[axis_change.axis]
            else:
                logger.warning(
                    "No detection found for axis %s, using config-based detection with empty evidence",
                    axis_change.axis,
                )
                detection_to_use = CharacteristicDetection(
                    axis=axis_def.axis,
                    detected_value=axis_def.original_value,
                    evidence_spans=[],
                    overall_confidence=1.0,
                )
        else:
            detection_to_use = CharacteristicDetection(
                axis=axis_def.axis,
                detected_value=axis_def.original_value,
                evidence_spans=[],
                overall_confidence=1.0,
            )

        result = await rewriter.rewrite_transcript(
            original_transcript=transcript_input,
            characteristic_detection=detection_to_use,
            axis_change=axis_change,
        )

        output_path = run_output_dir / f"counterfactual_{axis_def.axis}_{axis_def.target_value}.json"

        with output_path.open("w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)

        logger.info("Counterfactual saved to: %s", output_path)
        logger.info("Modified %d dialogue entries", len(result.evidence_spans_modified))

        html_report_path = run_output_dir / f"report_{axis_def.axis}_{axis_def.target_value}.html"
        generate_modification_report(result, html_report_path)
        logger.info("Modification report saved to: %s", html_report_path)

        results.append(result)

    logger.info("Output directory for this run: %s", run_output_dir)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate counterfactual transcript with attribute changes")
    parser.add_argument(
        "--config",
        type=str,
        default="default.yaml",
        help="Config file name in configs/ directory (default: default.yaml)",
    )
    args = parser.parse_args()

    config_path = WORKDIR / "configs" / args.config

    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise FileNotFoundError(msg)

    with config_path.open() as f:
        config_data = yaml.safe_load(f)

    config = CounterfactualConfig(**config_data)

    asyncio.run(generate_counterfactual_from_config(config))


if __name__ == "__main__":
    main()
