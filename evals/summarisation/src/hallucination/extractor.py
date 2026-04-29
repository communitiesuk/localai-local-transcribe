from __future__ import annotations

from evals.summarisation.src.hallucination.types import ClassifiedStatement


def build_statements(uncited_claims: list[str]) -> list[ClassifiedStatement]:
    """Maps uncited claims (already computed by common.templates.citations) to ClassifiedStatement objects."""
    return [
        ClassifiedStatement(
            hallucination_text=claim,
            citation_indices=[],
            hallucination_type="Unsupported",
            hallucination_reason="Could not find supporting evidence in the transcript",
        )
        for claim in uncited_claims
        if claim.strip()
    ]
