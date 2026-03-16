import logging

from common.database.postgres_models import DialogueEntry

logger = logging.getLogger(__name__)


def validate_evidence_spans(evidence_spans: list, max_index: int) -> None:
    """Validate evidence spans have valid indices and confidence scores."""
    for span in evidence_spans:
        if not hasattr(span, "dialogue_index"):
            continue

        if span.dialogue_index < 0 or span.dialogue_index >= max_index:
            msg = f"Evidence span index {span.dialogue_index} out of range [0, {max_index})"
            raise ValueError(msg)

        if hasattr(span, "confidence") and not 0.0 <= span.confidence <= 1.0:
            msg = f"Evidence span confidence {span.confidence} must be in [0.0, 1.0]"
            raise ValueError(msg)


def identify_modified_entries(
    original_entries: list[DialogueEntry],
    rewritten_entries: list[DialogueEntry],
) -> list[int]:
    """Return indices of dialogue entries with modified text."""
    modified_indices = []
    for i, (orig, rewritten) in enumerate(zip(original_entries, rewritten_entries, strict=False)):
        orig_text = orig["text"].strip()
        rewritten_text = rewritten["text"].strip()
        if orig_text != rewritten_text:
            modified_indices.append(i)
    return modified_indices
