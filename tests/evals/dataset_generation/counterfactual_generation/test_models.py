import pytest
from pydantic import ValidationError

from common.database.postgres_models import DialogueEntry
from evals.dataset_generation.counterfactual_generation.src.models import (
    AxisChange,
    CharacteristicDetection,
    CounterfactualOutput,
    EvidenceSpan,
    TranscriptInput,
)
from evals.dataset_generation.shared_constants import ProtectedCharacteristic


def test_evidence_span_initialization():
    span = EvidenceSpan(dialogue_index=0, text_snippet="test snippet", confidence=0.9)
    assert span.dialogue_index == 0
    assert span.text_snippet == "test snippet"
    assert span.confidence == 0.9


def test_evidence_span_confidence_validation_below_zero():
    with pytest.raises(ValidationError):
        EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=-0.1)


def test_evidence_span_confidence_validation_above_one():
    with pytest.raises(ValidationError):
        EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=1.5)


def test_evidence_span_confidence_at_boundaries():
    span_zero = EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=0.0)
    span_one = EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=1.0)
    assert span_zero.confidence == 0.0
    assert span_one.confidence == 1.0


def test_characteristic_detection_initialization():
    spans = [EvidenceSpan(dialogue_index=0, text_snippet="male pronoun", confidence=0.95)]
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.SEX,
        detected_value="male",
        evidence_spans=spans,
        overall_confidence=0.9,
    )
    assert detection.axis == ProtectedCharacteristic.SEX
    assert detection.detected_value == "male"
    assert len(detection.evidence_spans) == 1
    assert detection.overall_confidence == 0.9


def test_characteristic_detection_overall_confidence_validation():
    with pytest.raises(ValidationError):
        CharacteristicDetection(
            axis=ProtectedCharacteristic.AGE,
            detected_value="senior",
            evidence_spans=[],
            overall_confidence=1.2,
        )


def test_axis_change_initialization():
    change = AxisChange(
        axis=ProtectedCharacteristic.AGE,
        original_value="young",
        target_value="senior",
        instructions="Focus on age-related language",
    )
    assert change.axis == ProtectedCharacteristic.AGE
    assert change.original_value == "young"
    assert change.target_value == "senior"
    assert change.instructions == "Focus on age-related language"


def test_axis_change_optional_instructions():
    change = AxisChange(
        axis=ProtectedCharacteristic.RACE,
        original_value="white",
        target_value="black",
    )
    assert change.instructions is None


def test_transcript_input_initialization():
    entries = [
        DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Hi", start_time=1.0, end_time=2.0),
    ]
    transcript = TranscriptInput(dialogue_entries=entries, metadata={"source": "test"})
    assert len(transcript.dialogue_entries) == 2
    assert transcript.metadata["source"] == "test"


def test_transcript_input_default_metadata():
    entries = [DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0)]
    transcript = TranscriptInput(dialogue_entries=entries)
    assert transcript.metadata == {}


def test_counterfactual_output_initialization():
    original_entries = [DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0)]
    rewritten_entries = [DialogueEntry(speaker="A", text="Hi", start_time=0.0, end_time=1.0)]
    original_transcript = TranscriptInput(dialogue_entries=original_entries)
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.SEX,
        original_value="male",
        target_value="female",
    )

    output = CounterfactualOutput(
        original_transcript=original_transcript,
        rewritten_transcript=rewritten_entries,
        axis_change=axis_change,
        model_version="gpt-4",
        prompt_version="v1.0",
        evidence_spans_modified=[0],
    )

    assert output.original_transcript == original_transcript
    assert len(output.rewritten_transcript) == 1
    assert output.axis_change == axis_change
    assert output.model_version == "gpt-4"
    assert output.prompt_version == "v1.0"
    assert output.evidence_spans_modified == [0]


def test_counterfactual_output_default_evidence_spans_modified():
    original_entries = [DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0)]
    rewritten_entries = [DialogueEntry(speaker="A", text="Hi", start_time=0.0, end_time=1.0)]
    original_transcript = TranscriptInput(dialogue_entries=original_entries)
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.SEX,
        original_value="male",
        target_value="female",
    )

    output = CounterfactualOutput(
        original_transcript=original_transcript,
        rewritten_transcript=rewritten_entries,
        axis_change=axis_change,
        model_version="gpt-4",
        prompt_version="v1.0",
    )

    assert output.evidence_spans_modified == []


def test_evidence_span_requires_all_fields():
    with pytest.raises(ValidationError):
        EvidenceSpan(dialogue_index=0, text_snippet="test")

    with pytest.raises(ValidationError):
        EvidenceSpan(dialogue_index=0, confidence=0.9)

    with pytest.raises(ValidationError):
        EvidenceSpan(text_snippet="test", confidence=0.9)


def test_characteristic_detection_requires_all_fields():
    with pytest.raises(ValidationError):
        CharacteristicDetection(
            axis=ProtectedCharacteristic.AGE,
            detected_value="senior",
            evidence_spans=[],
        )


def test_axis_change_requires_core_fields():
    with pytest.raises(ValidationError):
        AxisChange(axis=ProtectedCharacteristic.AGE, original_value="young")

    with pytest.raises(ValidationError):
        AxisChange(axis=ProtectedCharacteristic.AGE, target_value="senior")
