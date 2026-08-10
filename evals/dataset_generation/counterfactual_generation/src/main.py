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
    The confidence reported by detection is carried through unchanged, because it is used
    later to choose between several records describing the same axis.
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
        overall_confidence=char_data["confidence"],
    )


def _load_characteristic_detections(
    detection_path: Path, dialogue_entries: list
) -> dict[ProtectedCharacteristic, list[CharacteristicDetection]]:
    """Load characteristic detections from file, grouped by axis.

    Detection reads the transcript in chunks, so a single axis normally appears many times in
    the output with different attribute values. Those values can be alternative wordings of
    one fact (for example "Asthma (chronic health condition)" and "Asthma (long-term health
    condition)") or genuinely different facts about different people (for example Female and
    Male on the Sex axis). Records that report the same attribute value are combined into one
    detection holding every evidence span found for that value and the highest confidence
    reported for it. Every value for an axis is returned so that the caller decides which one
    the rewrite should follow, rather than silently keeping whichever record came last.
    """
    logger.info("Loading characteristic detection from: %s", detection_path)
    with detection_path.open() as f:
        detection_data = json.load(f)

    detections_by_axis: dict[ProtectedCharacteristic, list[CharacteristicDetection]] = {}

    if "detected_characteristics" in detection_data:
        detected_chars = detection_data["detected_characteristics"]
        if detected_chars:
            logger.info("Found %d detected characteristics", len(detected_chars))
            detections_by_value: dict[tuple[ProtectedCharacteristic, str], CharacteristicDetection] = {}
            for char_data in detected_chars:
                detection = _convert_characteristics_schema(char_data, dialogue_entries)
                key = (detection.axis, detection.detected_value)
                already_seen = detections_by_value.get(key)
                if already_seen is None:
                    detections_by_value[key] = detection
                else:
                    already_seen.evidence_spans.extend(detection.evidence_spans)
                    already_seen.overall_confidence = max(already_seen.overall_confidence, detection.overall_confidence)
            for detection in detections_by_value.values():
                detections_by_axis.setdefault(detection.axis, []).append(detection)
            logger.info(
                "Grouped into %d distinct attribute values across %d axes",
                len(detections_by_value),
                len(detections_by_axis),
            )
        else:
            logger.warning("No characteristics detected in file, will use config-based axes")
    else:
        detection = CharacteristicDetection(**detection_data)
        detections_by_axis[detection.axis] = [detection]

    return detections_by_axis


def _select_detection(
    detections_for_axis: list[CharacteristicDetection],
    detection_attribute_value: str | None,
) -> CharacteristicDetection:
    """Choose which detection record for an axis should guide the rewrite.

    When the config names an attribute value, that exact record is used, which keeps a locked
    vector pinned to the evidence a reviewer checked it against. When no value is named, the
    record with the highest detection confidence is used, and the number of evidence spans
    breaks ties so that the better evidenced wording is preferred.
    """
    if detection_attribute_value is None:
        return max(
            detections_for_axis,
            key=lambda detection: (detection.overall_confidence, len(detection.evidence_spans)),
        )

    for detection in detections_for_axis:
        if detection.detected_value == detection_attribute_value:
            return detection

    available_values = [detection.detected_value for detection in detections_for_axis]
    msg = (
        f"Config names detection attribute value {detection_attribute_value!r} for axis "
        f"{detections_for_axis[0].axis}, but detection reported: {available_values}"
    )
    raise ValueError(msg)


def _load_transcript(transcript_path: Path) -> TranscriptInput:
    """Load a transcript file and return its dialogue together with its source provenance.

    Everything in the file other than the dialogue itself describes how that transcript was
    generated, such as its theme and its actor definitions. That description is kept, along with
    the transcript identifier and path, because otherwise a counterfactual file records nothing
    about which transcript it was derived from.
    """
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

    source_metadata = (
        {key: value for key, value in transcript_data.items() if key != "dialogue_entries"}
        if isinstance(transcript_data, dict)
        else {}
    )
    source_metadata["source_transcript_id"] = transcript_path.stem
    source_metadata["source_transcript_path"] = str(transcript_path)

    return TranscriptInput(dialogue_entries=dialogue_entries, metadata=source_metadata)


async def generate_counterfactual_from_config(config: CounterfactualConfig) -> list[CounterfactualOutput]:
    transcript_path = config.get_transcript_path(PROJECT_ROOT)
    transcript_input = _load_transcript(transcript_path)

    characteristic_detection_path = config.get_characteristic_detection_path(PROJECT_ROOT)
    if characteristic_detection_path:
        detections_by_axis = _load_characteristic_detections(
            characteristic_detection_path, transcript_input.dialogue_entries
        )
    else:
        logger.info("No characteristic detection file provided, using config-based axes")
        detections_by_axis = {}

    # The transcript identifier leads the directory name so that a run can be attributed to its
    # source transcript from the path alone, and so that repeating one transcript after a failure
    # produces a directory that is obviously a second attempt at that same transcript.
    run_timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    run_output_dir = WORKDIR / "output" / f"{transcript_path.stem}_{run_timestamp}"
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
                detection_to_use = _select_detection(
                    detections_by_axis[axis_change.axis], axis_def.detection_attribute_value
                )
                logger.info(
                    "Using detection value %r (confidence %.2f, %d evidence spans)",
                    detection_to_use.detected_value,
                    detection_to_use.overall_confidence,
                    len(detection_to_use.evidence_spans),
                )
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

        # An axis enum formats as its member name inside an f-string, so the readable value is used
        # instead. The transcript identifier is repeated in the file name so that a counterfactual
        # stays identifiable if these files are later gathered into one directory, where many
        # transcripts produce the same axis and target pair.
        axis_file_label = axis_def.axis.value.replace(" ", "_")
        output_stem = f"{transcript_path.stem}_{axis_file_label}_{axis_def.target_value}"

        output_path = run_output_dir / f"counterfactual_{output_stem}.json"

        with output_path.open("w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)

        logger.info("Counterfactual saved to: %s", output_path)
        logger.info("Modified %d dialogue entries", len(result.evidence_spans_modified))

        html_report_path = run_output_dir / f"report_{output_stem}.html"
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
