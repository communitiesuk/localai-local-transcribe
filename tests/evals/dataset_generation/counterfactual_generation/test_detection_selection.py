import json

import pytest

from evals.dataset_generation.counterfactual_generation.src.main import (
    _load_characteristic_detections,
    _select_detection,
)
from evals.dataset_generation.counterfactual_generation.src.models import CharacteristicDetection
from evals.dataset_generation.shared_constants import ProtectedCharacteristic

# The loader reconstructs the transcript as "speaker: text" entries joined by newlines, then maps
# character offsets back to entry indices. "Officer: We spoke about her asthma" is 34 characters,
# so the first entry covers offsets 0 to 33 and the second entry starts at offset 35. Spans in the
# tests below sit inside one of those two ranges, because a span that falls on the joining newline
# belongs to no entry and is discarded.
DIALOGUE_ENTRIES = [
    {"speaker": "Officer", "text": "We spoke about her asthma"},
    {"speaker": "Tenant", "text": "Yes, and the damp makes it worse"},
]


def _write_detection_file(tmp_path, detected_characteristics):
    """Write a characteristics detection output file and return its path."""
    detection_path = tmp_path / "detection.json"
    detection_path.write_text(
        json.dumps({"version": "1.0", "metadata": {}, "detected_characteristics": detected_characteristics})
    )
    return detection_path


def _characteristic(characteristic, attribute_value, confidence, spans):
    """Build one detected characteristic record in the characteristics detection schema."""
    return {
        "characteristic": characteristic,
        "attribute_value": attribute_value,
        "confidence": confidence,
        "evidence_spans": [{"start_index": start, "end_index": end, "text": text} for start, end, text in spans],
    }


def test_loader_keeps_every_attribute_value_for_an_axis(tmp_path):
    detection_path = _write_detection_file(
        tmp_path,
        [
            _characteristic("Sex", "Female", 0.9, [(0, 10, "her asthma")]),
            _characteristic("Sex", "Male", 0.8, [(51, 59, "the damp")]),
        ],
    )

    detections_by_axis = _load_characteristic_detections(detection_path, DIALOGUE_ENTRIES)

    detected_values = {detection.detected_value for detection in detections_by_axis[ProtectedCharacteristic.SEX]}
    assert detected_values == {"Female", "Male"}


def test_loader_merges_records_that_share_an_attribute_value(tmp_path):
    detection_path = _write_detection_file(
        tmp_path,
        [
            _characteristic("Disability", "Asthma", 0.6, [(0, 10, "her asthma")]),
            _characteristic("Disability", "Asthma", 0.95, [(51, 59, "the damp")]),
        ],
    )

    detections_by_axis = _load_characteristic_detections(detection_path, DIALOGUE_ENTRIES)
    merged = detections_by_axis[ProtectedCharacteristic.DISABILITY]

    assert len(merged) == 1
    assert len(merged[0].evidence_spans) == 2
    assert merged[0].overall_confidence == 0.95


def test_loader_carries_detection_confidence(tmp_path):
    detection_path = _write_detection_file(
        tmp_path, [_characteristic("Race", "White British", 0.65, [(0, 10, "her asthma")])]
    )

    detections_by_axis = _load_characteristic_detections(detection_path, DIALOGUE_ENTRIES)

    assert detections_by_axis[ProtectedCharacteristic.RACE][0].overall_confidence == 0.65


def test_select_detection_uses_named_attribute_value():
    detections_for_axis = [
        CharacteristicDetection(
            axis=ProtectedCharacteristic.SEX, detected_value="Female", evidence_spans=[], overall_confidence=0.4
        ),
        CharacteristicDetection(
            axis=ProtectedCharacteristic.SEX, detected_value="Male", evidence_spans=[], overall_confidence=0.9
        ),
    ]

    selected = _select_detection(detections_for_axis, "Female")

    assert selected.detected_value == "Female"


def test_select_detection_falls_back_to_highest_confidence_when_unnamed():
    detections_for_axis = [
        CharacteristicDetection(
            axis=ProtectedCharacteristic.AGE, detected_value="Older person", evidence_spans=[], overall_confidence=0.5
        ),
        CharacteristicDetection(
            axis=ProtectedCharacteristic.AGE, detected_value="Adult", evidence_spans=[], overall_confidence=0.85
        ),
    ]

    selected = _select_detection(detections_for_axis, None)

    assert selected.detected_value == "Adult"


def test_select_detection_raises_for_unknown_attribute_value():
    detections_for_axis = [
        CharacteristicDetection(
            axis=ProtectedCharacteristic.SEX, detected_value="Female", evidence_spans=[], overall_confidence=0.9
        )
    ]

    with pytest.raises(ValueError, match="but detection reported"):
        _select_detection(detections_for_axis, "Nonexistent value")
