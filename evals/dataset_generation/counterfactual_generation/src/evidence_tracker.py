import logging

from common.database.postgres_models import DialogueEntry

logger = logging.getLogger(__name__)


def verify_evidence_modifications(
    evidence_spans: list,
    modified_indices: list[int],
    original_entries: list[DialogueEntry],
    rewritten_entries: list[DialogueEntry],
) -> None:
    """Evidence modification tracking for counterfactual transcript rewriting."""
    if not evidence_spans:
        return

    if hasattr(evidence_spans[0], "dialogue_index"):
        _verify_index_based_evidence(evidence_spans, modified_indices)
    else:
        logger.info(
            "Evidence spans provided as text snippets (not dialogue indices). "
            "Checking if evidence text appears in modified entries..."
        )
        _verify_text_based_evidence(evidence_spans, modified_indices, original_entries, rewritten_entries)


def _verify_index_based_evidence(evidence_spans: list, modified_indices: list[int]) -> None:
    """Verify modifications for dialogue-index-based evidence spans."""
    evidence_indices = {span.dialogue_index for span in evidence_spans}
    modified_set = set(modified_indices)

    unmodified_evidence = evidence_indices - modified_set
    if unmodified_evidence:
        logger.warning(
            "Evidence spans at indices %s were not modified",
            sorted(unmodified_evidence),
        )

    modification_rate = len(evidence_indices & modified_set) / len(evidence_indices) if evidence_indices else 0
    logger.info(
        "Modified %d/%d evidence-based entries (%.1f%%)",
        len(evidence_indices & modified_set),
        len(evidence_indices),
        modification_rate * 100,
    )


def _verify_text_based_evidence(
    evidence_spans: list,
    modified_indices: list[int],
    original_entries: list[DialogueEntry],
    rewritten_entries: list[DialogueEntry],
) -> None:
    """Verify modifications for text-based evidence spans by searching for text snippets."""
    evidence_texts = [getattr(span, "text_snippet", None) or getattr(span, "text", "") for span in evidence_spans]
    evidence_texts = [text for text in evidence_texts if text]

    if not evidence_texts:
        logger.warning("No text content found in evidence spans")
        return

    modified_with_evidence = 0
    total_evidence_found = 0

    for evidence_text in evidence_texts:
        if not evidence_text:
            continue
        found_in_original = False
        found_in_modified = False

        for idx in modified_indices:
            original_text = original_entries[idx].get("text", "")
            if evidence_text in original_text:
                found_in_original = True
                total_evidence_found += 1
                rewritten_text = rewritten_entries[idx].get("text", "")
                if original_text != rewritten_text:
                    found_in_modified = True
                    modified_with_evidence += 1
                break

        if found_in_original and not found_in_modified:
            logger.debug("Evidence text not modified: %s", evidence_text[:50])

    if total_evidence_found > 0:
        modification_rate = (modified_with_evidence / total_evidence_found) * 100
        logger.info(
            "Modified %d/%d evidence-containing entries (%.1f%%)",
            modified_with_evidence,
            total_evidence_found,
            modification_rate,
        )
    else:
        logger.warning(
            "None of the %d evidence text snippets were found in the transcript",
            len(evidence_texts),
        )
