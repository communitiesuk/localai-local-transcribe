from common.database.postgres_models import DialogueEntry
from evals.dataset_generation.counterfactual_generation.src.evidence_tracker import (
    _verify_index_based_evidence,
    _verify_text_based_evidence,
    verify_evidence_modifications,
)
from evals.dataset_generation.counterfactual_generation.src.models import EvidenceSpan


def test_verify_evidence_modifications_with_empty_evidence_spans():
    original = [DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0)]
    rewritten = [DialogueEntry(speaker="A", text="Hi", start_time=0.0, end_time=1.0)]
    verify_evidence_modifications([], [0], original, rewritten)


def test_verify_evidence_modifications_with_index_based_evidence():
    spans = [
        EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=0.9),
        EvidenceSpan(dialogue_index=2, text_snippet="another", confidence=0.8),
    ]
    original = [
        DialogueEntry(speaker="A", text="test", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="middle", start_time=1.0, end_time=2.0),
        DialogueEntry(speaker="C", text="another", start_time=2.0, end_time=3.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="modified", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="middle", start_time=1.0, end_time=2.0),
        DialogueEntry(speaker="C", text="changed", start_time=2.0, end_time=3.0),
    ]
    verify_evidence_modifications(spans, [0, 2], original, rewritten)


def test_verify_evidence_modifications_with_text_based_evidence():
    class TextSpan:
        text_snippet = "evidence text"

    spans = [TextSpan()]
    original = [
        DialogueEntry(speaker="A", text="This has evidence text in it", start_time=0.0, end_time=1.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="This has modified text in it", start_time=0.0, end_time=1.0),
    ]
    verify_evidence_modifications(spans, [0], original, rewritten)


def test_verify_index_based_evidence_all_modified(caplog):
    import logging

    caplog.set_level(logging.INFO)
    spans = [
        EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=0.9),
        EvidenceSpan(dialogue_index=1, text_snippet="another", confidence=0.8),
    ]
    modified_indices = [0, 1]
    _verify_index_based_evidence(spans, modified_indices)
    assert "Modified 2/2 evidence-based entries (100.0%)" in caplog.text


def test_verify_index_based_evidence_partial_modification(caplog):
    import logging

    caplog.set_level(logging.INFO)
    spans = [
        EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=0.9),
        EvidenceSpan(dialogue_index=1, text_snippet="another", confidence=0.8),
        EvidenceSpan(dialogue_index=2, text_snippet="third", confidence=0.7),
    ]
    modified_indices = [0, 2]
    _verify_index_based_evidence(spans, modified_indices)
    assert "Evidence spans at indices [1] were not modified" in caplog.text
    assert "Modified 2/3 evidence-based entries (66.7%)" in caplog.text


def test_verify_index_based_evidence_none_modified(caplog):
    import logging

    caplog.set_level(logging.INFO)
    spans = [
        EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=0.9),
    ]
    modified_indices = [1, 2]
    _verify_index_based_evidence(spans, modified_indices)
    assert "Evidence spans at indices [0] were not modified" in caplog.text
    assert "Modified 0/1 evidence-based entries (0.0%)" in caplog.text


def test_verify_index_based_evidence_empty_spans():
    _verify_index_based_evidence([], [0, 1])


def test_verify_text_based_evidence_found_and_modified(caplog):
    import logging

    caplog.set_level(logging.INFO)

    class TextSpan:
        text_snippet = "evidence"

    spans = [TextSpan()]
    original = [
        DialogueEntry(speaker="A", text="This has evidence in it", start_time=0.0, end_time=1.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="This has modified text", start_time=0.0, end_time=1.0),
    ]
    _verify_text_based_evidence(spans, [0], original, rewritten)
    assert "Modified 1/1 evidence-containing entries (100.0%)" in caplog.text


def test_verify_text_based_evidence_found_but_not_modified(caplog):
    import logging

    caplog.set_level(logging.INFO)

    class TextSpan:
        text_snippet = "evidence"

    spans = [TextSpan()]
    original = [
        DialogueEntry(speaker="A", text="This has evidence in it", start_time=0.0, end_time=1.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="This has evidence in it", start_time=0.0, end_time=1.0),
    ]
    _verify_text_based_evidence(spans, [0], original, rewritten)
    assert "Modified 0/1 evidence-containing entries (0.0%)" in caplog.text


def test_verify_text_based_evidence_not_found(caplog):
    class TextSpan:
        text_snippet = "missing"

    spans = [TextSpan()]
    original = [
        DialogueEntry(speaker="A", text="This has no match", start_time=0.0, end_time=1.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="This has no match", start_time=0.0, end_time=1.0),
    ]
    _verify_text_based_evidence(spans, [0], original, rewritten)
    assert "None of the 1 evidence text snippets were found" in caplog.text


def test_verify_text_based_evidence_empty_text_snippets(caplog):
    class EmptySpan:
        text_snippet = ""

    spans = [EmptySpan()]
    original = [DialogueEntry(speaker="A", text="Text", start_time=0.0, end_time=1.0)]
    rewritten = [DialogueEntry(speaker="A", text="Text", start_time=0.0, end_time=1.0)]
    _verify_text_based_evidence(spans, [0], original, rewritten)
    assert "No text content found in evidence spans" in caplog.text


def test_verify_text_based_evidence_with_text_attribute():
    class TextSpan:
        text = "evidence text"

    spans = [TextSpan()]
    original = [
        DialogueEntry(speaker="A", text="This has evidence text", start_time=0.0, end_time=1.0),
    ]
    rewritten = [
        DialogueEntry(speaker="A", text="Modified", start_time=0.0, end_time=1.0),
    ]
    _verify_text_based_evidence(spans, [0], original, rewritten)
