from __future__ import annotations

import re

from common.database.postgres_models import DialogueEntry
from common.format_transcript import transcript_as_index_speaker_and_utterance

# A citation marker as the production citation step writes it: a single entry index, or a span
# written by ``combine_consecutive_citations``. That function merges indices up to
# ``MAX_CITATION_DISTANCE`` apart, so ``[4-6]`` runs from the first to the last cited entry and may
# skip entries in between. The comma form is matched too: the citing model emits it despite
# ``cite_claims.j2`` asking for ``[80][81]``, and nothing downstream normalises it away.
_CITATION_MARKER_RE = re.compile(r"\[\d+(?:\s*[-,]\s*\d+)*\]")
_MARKER_INDEX_RE = re.compile(r"\d+")

# One line of ``transcript_as_index_speaker_and_utterance`` output: ``[n] Speaker: utterance``.
_ENTRY_LINE_RE = re.compile(r"^\[(\d+)\] ", re.MULTILINE)


def judge_transcript_text(dialogue_entries: list[DialogueEntry]) -> str:
    """Render a transcript for the LLM judge, numbered exactly as the citation step numbers it.

    The production summariser cites claims with ``[n]`` markers, where ``n`` is the index of a
    transcript entry as numbered by ``transcript_as_index_speaker_and_utterance``. The judge has to
    see that same numbering: given an unnumbered transcript it cannot resolve a marker to an entry,
    so its auditability score reflects its own inability to verify rather than how traceable the
    summary is. Reusing the production formatter keeps the two views in step by construction.
    """
    return transcript_as_index_speaker_and_utterance(dialogue_entries)


def transcript_entry_count(transcript_text: str) -> int:
    """Number of entries in a transcript rendered by :func:`judge_transcript_text`."""
    return len(_ENTRY_LINE_RE.findall(transcript_text))


def citation_markers(summary_text: str, n_entries: int) -> list[str]:
    """Distinct citation markers in ``summary_text`` that resolve to one of ``n_entries`` entries.

    Whether a summary carries citations is a fact about the text, not a judgement, and it must be
    established mechanically before the judge sees it. Not every summariser path emits markers:
    templates with ``citations_required = False`` and the basic-minutes fallback produce none. Asked
    to score the traceability of such a summary against a numbered transcript, the judge invents
    markers and then credits them — an observed run scored 4.2/5 on rationales citing entries that
    the summary never referenced. Handing it this list instead removes the room to imagine evidence.

    Markers are bounded against the transcript because the pattern cannot tell a citation from any
    other bracketed number: unbounded, ``the [2024-2025] budget`` in an uncited summary would be
    reported to the judge as a citation and send it off to resolve entry 2024. Duplicates are
    collapsed so the count reads as coverage rather than as a tally of occurrences.
    """
    resolvable = [
        marker
        for marker in _CITATION_MARKER_RE.findall(summary_text)
        if all(int(index) < n_entries for index in _MARKER_INDEX_RE.findall(marker))
    ]
    return list(dict.fromkeys(resolvable))
