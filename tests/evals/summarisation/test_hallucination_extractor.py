from __future__ import annotations

from evals.summarisation.src.hallucination.extractor import build_statements


def test_build_statements_maps_uncited_claims():
    results = build_statements(["The unicorn Sparklehoof was mentioned", "Next meeting is TBD"])
    assert len(results) == 2
    for stmt in results:
        assert stmt.hallucination_type == "Unsupported"
        assert stmt.citation_indices == []
        assert stmt.hallucination_reason == "Could not find supporting evidence in the transcript"


def test_build_statements_empty():
    assert build_statements([]) == []


def test_build_statements_skips_blank_claims():
    assert build_statements(["", "  ", "Valid claim"]) == [build_statements(["Valid claim"])[0]]


def test_build_statements_preserves_text():
    results = build_statements(["Person1 mentioned their unicorn Sparklehoof"])
    assert results[0].hallucination_text == "Person1 mentioned their unicorn Sparklehoof"
