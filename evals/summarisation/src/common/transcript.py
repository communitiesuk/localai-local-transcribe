from __future__ import annotations

import re

from common.database.postgres_models import DialogueEntry
from common.format_transcript import transcript_as_index_speaker_and_utterance

# A citation marker as the production citation step writes it: a single entry index, or a range
# collapsed from consecutive indices by ``combine_consecutive_citations``.
_CITATION_MARKER_RE = re.compile(r"\[\d+(?:-\d+)?\]")


def judge_transcript_text(dialogue_entries: list[DialogueEntry]) -> str:
    """Render a transcript for the LLM judge, numbered exactly as the citation step numbers it.

    The production summariser cites claims with ``[n]`` markers, where ``n`` is the index of a
    transcript entry as numbered by ``transcript_as_index_speaker_and_utterance``. The judge has to
    see that same numbering: given an unnumbered transcript it cannot resolve a marker to an entry,
    so its auditability score reflects its own inability to verify rather than how traceable the
    summary is. Reusing the production formatter keeps the two views in step by construction.
    """
    return transcript_as_index_speaker_and_utterance(dialogue_entries)


def citation_markers(summary_text: str) -> list[str]:
    """Return the citation markers literally present in ``summary_text``, in order of appearance.

    Whether a summary carries citations is a fact about the text, not a judgement, and it must be
    established mechanically before the judge sees it. Not every summariser path emits markers:
    templates with ``citations_required = False`` and the basic-minutes fallback produce none. Asked
    to score the traceability of such a summary against a numbered transcript, the judge invents
    markers and then credits them — an observed run scored 4.2/5 on rationales citing entries that
    the summary never referenced. Handing it this list instead removes the room to imagine evidence.
    """
    return _CITATION_MARKER_RE.findall(summary_text)
