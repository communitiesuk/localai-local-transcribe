import pytest

from common.database.postgres_models import DialogueEntry
from evals.dataset_generation.counterfactual_generation.src.models import EvidenceSpan
from evals.dataset_generation.counterfactual_generation.src.validation import (
    identify_modified_entries,
    validate_evidence_spans,
)


def test_validate_evidence_spans_valid():
    spans = [
        EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=0.9),
        EvidenceSpan(dialogue_index=2, text_snippet="another", confidence=0.8),
    ]
    result = validate_evidence_spans(spans, max_index=5)
    assert result is None


def test_validate_evidence_spans_index_out_of_range_negative():
    spans = [EvidenceSpan(dialogue_index=-1, text_snippet="test", confidence=0.9)]
    with pytest.raises(ValueError, match="Evidence span index -1 out of range"):
        validate_evidence_spans(spans, max_index=5)


def test_validate_evidence_spans_index_out_of_range_too_high():
    spans = [EvidenceSpan(dialogue_index=5, text_snippet="test", confidence=0.9)]
    with pytest.raises(ValueError, match="Evidence span index 5 out of range"):
        validate_evidence_spans(spans, max_index=5)


def test_validate_evidence_spans_confidence_at_boundaries():
    spans = [
        EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=0.0),
        EvidenceSpan(dialogue_index=1, text_snippet="test", confidence=1.0),
    ]
    result = validate_evidence_spans(spans, max_index=5)
    assert result is None


def test_validate_evidence_spans_empty_list():
    result = validate_evidence_spans([], max_index=5)
    assert result is None


def test_validate_evidence_spans_without_dialogue_index():
    class SimpleSpan:
        text_snippet = "test"
        confidence = 0.9

    spans = [SimpleSpan()]
    result = validate_evidence_spans(spans, max_index=5)
    assert result is None


def test_identify_modified_entries_no_modifications():
    original = [
        DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Hi there", start_time=1.0, end_time=2.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Hi there", start_time=1.0, end_time=2.0),
    ]
    result = identify_modified_entries(original, rewritten)
    assert result == []


def test_identify_modified_entries_all_modified():
    original = [
        DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Hi there", start_time=1.0, end_time=2.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="Greetings", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Hello friend", start_time=1.0, end_time=2.0),
    ]
    result = identify_modified_entries(original, rewritten)
    assert result == [0, 1]


def test_identify_modified_entries_partial_modifications():
    original = [
        DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Hi there", start_time=1.0, end_time=2.0),
        DialogueEntry(speaker="C", text="Good day", start_time=2.0, end_time=3.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Hello everyone", start_time=1.0, end_time=2.0),
        DialogueEntry(speaker="C", text="Good day", start_time=2.0, end_time=3.0),
    ]
    result = identify_modified_entries(original, rewritten)
    assert result == [1]


def test_identify_modified_entries_whitespace_only_changes():
    original = [
        DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text=" Hello ", start_time=0.0, end_time=1.0),
    ]
    result = identify_modified_entries(original, rewritten)
    assert result == []


def test_identify_modified_entries_empty_lists():
    result = identify_modified_entries([], [])
    assert result == []


def test_identify_modified_entries_preserves_order():
    original = [
        DialogueEntry(speaker="A", text="One", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Two", start_time=1.0, end_time=2.0),
        DialogueEntry(speaker="C", text="Three", start_time=2.0, end_time=3.0),
        DialogueEntry(speaker="D", text="Four", start_time=3.0, end_time=4.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="Modified One", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Two", start_time=1.0, end_time=2.0),
        DialogueEntry(speaker="C", text="Modified Three", start_time=2.0, end_time=3.0),
        DialogueEntry(speaker="D", text="Four", start_time=3.0, end_time=4.0),
    ]
    result = identify_modified_entries(original, rewritten)
    assert result == [0, 2]
