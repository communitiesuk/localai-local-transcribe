from common.database.postgres_models import ContentSource
from common.types import FailureCategory

FACTUAL_INTEGRITY_MESSAGE = (
    "Review carefully: there might be problems with the quality of information in this document."
)
REQUIRED_CONTENT_AND_STRUCTURE_MESSAGE = "Review carefully: this document may be missing important information."
INSTRUCTION_INTEGRITY_MESSAGE = (
    "Review carefully: the transcript or template may have influenced the AI unintentionally."
)
EVIDENCE_AND_CITATION_QUALITY_MESSAGE = (
    "Review carefully: some claims may not have a linked quote, or the quote may be inaccurate."
)
DATA_PROTECTION_MESSAGE = "Review carefully: this document may include personal data you wanted to exclude."
OPERATIONAL_SIGNALS_MESSAGE = (
    "Review carefully: the AI tried and failed to check the document, so it might contain inaccuracies."
)
EDIT_SAFETY_AND_INTENT_MESSAGE = "Something went wrong with the AI edit – try providing a different instruction."
MULTIPLE_FAILURES_MESSAGE = (
    "Check your transcript and template – the AI spotted various issues when generating your document, "
    "which might make it unreliable."
)

_MESSAGE_BY_CATEGORY = {
    FailureCategory.FACTUAL_INTEGRITY.value: FACTUAL_INTEGRITY_MESSAGE,
    FailureCategory.REQUIRED_CONTENT_AND_STRUCTURE.value: REQUIRED_CONTENT_AND_STRUCTURE_MESSAGE,
    FailureCategory.INSTRUCTION_INTEGRITY.value: INSTRUCTION_INTEGRITY_MESSAGE,
    FailureCategory.EVIDENCE_AND_CITATION_QUALITY.value: EVIDENCE_AND_CITATION_QUALITY_MESSAGE,
    FailureCategory.DATA_PROTECTION.value: DATA_PROTECTION_MESSAGE,
    FailureCategory.EDIT_SAFETY_AND_INTENT.value: EDIT_SAFETY_AND_INTENT_MESSAGE,
}


def get_guardrail_warning_message(
    *,
    content_source: ContentSource,
    categories: set[str],
    previous_version_has_issues: bool = False,
    guardrail_failed: bool = False,
) -> str | None:
    if content_source == ContentSource.MANUAL_EDIT:
        return None

    if not categories:
        return OPERATIONAL_SIGNALS_MESSAGE if guardrail_failed else None

    known_categories = categories & set(_MESSAGE_BY_CATEGORY)
    if not known_categories:
        return None

    if len(known_categories) == 1:
        return _MESSAGE_BY_CATEGORY[next(iter(known_categories))]

    if content_source == ContentSource.AI_EDIT and not previous_version_has_issues:
        return EDIT_SAFETY_AND_INTENT_MESSAGE

    return MULTIPLE_FAILURES_MESSAGE
