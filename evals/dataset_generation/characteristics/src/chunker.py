import re
from pathlib import Path

from common.llm.client import ChatBot
from evals.dataset_generation.characteristics.src.config_loader import render_prompt
from evals.dataset_generation.characteristics.src.schema import (
    CharacteristicDetection,
    CharacteristicExtractionOutput,
    TextSpan,
)


def find_spans(text: str, transcript: str) -> list[tuple[int, int]]:
    """Find all occurrences of text in transcript, returning (start, end) index tuples."""
    pattern = re.escape(text.strip())
    return [(m.start(), m.end()) for m in re.finditer(pattern, transcript)]


_ARTICLE_PREFIX_RE = re.compile(r"(?<!\w)(an|a|the|my|our|your) $", re.IGNORECASE)


def _article_extended_start(match_start: int, text: str) -> int:
    """Extend a span start leftward to include a leading article or possessive if present.

    Fixes model tendency to strip determiners: 'amputee' → 'an amputee',
    'gender identity' → 'my gender identity', 'age' → 'our age'.
    """
    m = _ARTICLE_PREFIX_RE.search(text[:match_start])
    return m.start() if m else match_start


# Minimum original span-text length to allow multi-occurrence expansion within a chunk.
# Short common words (pronouns, articles ≤3 chars) are excluded to prevent FP explosions
# when the same pronoun appears dozens of times in the same passage.
_MIN_MULTI_OCCURRENCE_LEN = 4


def _located_spans(detection: "CharacteristicDetection") -> list[tuple[int, int]]:
    """Return (start, end) pairs for spans that have been located in the transcript."""
    return [
        (s.start_index, s.end_index)
        for s in detection.evidence_spans
        if s.start_index is not None and s.end_index is not None
    ]


def _spans_related(a: "CharacteristicDetection", b: "CharacteristicDetection") -> bool:
    """Return True if any span in `a` contains or is contained by any span in `b`.

    This catches sub-span duplicates (e.g. 'Blum' inside 'Mrs Blum', 'with disabilities'
    inside 'individuals with disabilities') so they are merged rather than counted separately.
    """
    return any(
        (a_s <= b_s and a_e >= b_e) or (b_s <= a_s and b_e >= a_e)
        for a_s, a_e in _located_spans(a)
        for b_s, b_e in _located_spans(b)
    )


def _remove_subspans(spans: list[TextSpan]) -> list[TextSpan]:
    """Remove spans that are strictly contained within a longer span in the same list."""
    positions = [(s.start_index, s.end_index) for s in spans if s.start_index is not None and s.end_index is not None]

    def subsumed(start: int, end: int) -> bool:
        return any(o_s <= start and o_e >= end and (o_s, o_e) != (start, end) for o_s, o_e in positions)

    return [
        s for s in spans if s.start_index is None or s.end_index is None or not subsumed(s.start_index, s.end_index)
    ]


# Maximum character length a container span may have for the upgrade to fire.
# Names and titles are short (e.g. "Mrs Blum" = 8 chars, "Rabbi Moshe Levi" = 16 chars).
# Long disability or characteristic phrases are NOT eligible as upgrade targets — promoting
# "an amputee" into a 60-char sentence would turn a correct short span into a wide FP.
_MAX_UPGRADE_SPAN_LEN = 25


def _upgrade_subspans_to_longest(entries: list[CharacteristicDetection]) -> list[CharacteristicDetection]:
    """Replace short contained spans with the longest *name-length* span that contains them.

    Only upgrades when the containing span is short (≤ _MAX_UPGRADE_SPAN_LEN chars) so that
    name sub-spans ('Blum' → 'Mrs Blum') are consolidated without accidentally promoting
    correct short disability phrases into long incorrect sentences.
    """
    all_located: list[tuple[int, int, str]] = [
        (s.start_index, s.end_index, s.text)
        for e in entries
        for s in e.evidence_spans
        if s.start_index is not None and s.end_index is not None
    ]

    def best_name_container(start: int, end: int) -> tuple[int, int, str] | None:
        candidates = [
            (s, e, t)
            for s, e, t in all_located
            if s <= start and e >= end and (s < start or e > end) and (e - s) <= _MAX_UPGRADE_SPAN_LEN
        ]
        return max(candidates, key=lambda x: x[1] - x[0], default=None)

    for entry in entries:
        for span in entry.evidence_spans:
            if span.start_index is None or span.end_index is None:
                continue
            container = best_name_container(span.start_index, span.end_index)
            if container is not None:
                span.start_index, span.end_index, span.text = container
    return entries


def deduplicate_characteristics(characteristics: list[CharacteristicDetection]) -> list[CharacteristicDetection]:
    """Merge characteristics with the same category and value, combining their evidence spans.

    Four levels of consolidation:
    1. Exact (characteristic, attribute_value) duplicates — spans are merged.
    2. Same characteristic with related spans (exact match, containment, or containment by a
       larger span) — merged, keeping the highest-confidence attribute_value.
    3. Cross-characteristic span upgrade — sub-spans are promoted to the longest containing
       span found anywhere in the hypothesis (e.g. 'Blum' → 'Mrs Blum').
    4. Sub-span cleanup within each entry — spans fully enclosed by a longer sibling are dropped.
    """
    by_value: dict[str, CharacteristicDetection] = {}

    for item in characteristics:
        signature = f"{item.characteristic}|{item.attribute_value}"

        if signature in by_value:
            seen_positions = {(s.start_index, s.end_index) for s in by_value[signature].evidence_spans}
            for span in item.evidence_spans:
                pos = (span.start_index, span.end_index)
                if pos not in seen_positions:
                    by_value[signature].evidence_spans.append(span)
                    seen_positions.add(pos)
        else:
            by_value[signature] = item

    result: list[CharacteristicDetection] = []
    for candidate in by_value.values():
        merged_into = next(
            (
                existing
                for existing in result
                if existing.characteristic == candidate.characteristic and _spans_related(existing, candidate)
            ),
            None,
        )
        if merged_into is not None:
            if candidate.confidence > merged_into.confidence:
                merged_into.attribute_value = candidate.attribute_value
                merged_into.confidence = candidate.confidence
            seen_positions = {(s.start_index, s.end_index) for s in merged_into.evidence_spans}
            for span in candidate.evidence_spans:
                pos = (span.start_index, span.end_index)
                if pos not in seen_positions:
                    merged_into.evidence_spans.append(span)
                    seen_positions.add(pos)
        else:
            result.append(candidate)

    _upgrade_subspans_to_longest(result)

    for item in result:
        item.evidence_spans = _remove_subspans(item.evidence_spans)

    return result


_MAX_WORD_ALIGN_CHARS = 30


def _align_to_word_start(transcript: str, pos: int) -> int:
    """Advance pos to the start of the next word if currently mid-word.

    Prevents chunks from starting with a partial word (e.g. "uals with disabilities"
    instead of "individuals with disabilities") which causes garbled model output.
    Only advances up to _MAX_WORD_ALIGN_CHARS; if no space is found within that
    window the original position is returned unchanged.
    """
    if pos == 0 or not transcript[pos - 1 : pos].isalnum():
        return pos
    space = transcript.find(" ", pos)
    if space == -1 or space - pos > _MAX_WORD_ALIGN_CHARS:
        return pos
    return space + 1


def build_chunks(transcript: str, chunk_size_chars: int = 1000, overlap_chars: int = 400) -> list[tuple[str, int]]:
    stride = chunk_size_chars - overlap_chars
    chunks = []
    start = 0
    while start < len(transcript):
        aligned = _align_to_word_start(transcript, start)
        if aligned >= len(transcript):
            break
        chunks.append((transcript[aligned : aligned + chunk_size_chars], aligned))
        start += stride
    return chunks


_LEADING_WITH_POSSESSIVE_RE = re.compile(r"^With\s+(my|your|our|his|her)\s", re.IGNORECASE)


def _strip_leading_with(start: int, end: int, chunk: str) -> int:
    """Advance start past a leading 'With my/your/our' prefix in P&M-style spans.

    The model sometimes returns 'With my first' when the reference expects 'my first'.
    Strip 'With ' when it immediately precedes a possessive pronoun.
    """
    span_text = chunk[start:end]
    m = _LEADING_WITH_POSSESSIVE_RE.match(span_text)
    if m:
        return start + m.start(1)
    return start


def _find_new_positions(text: str, chunk: str, used: set[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return positions of all not-yet-claimed occurrences of text in chunk, marking them used."""
    result = []
    for m in re.finditer(re.escape(text), chunk):
        start = _article_extended_start(m.start(), chunk)
        start = _strip_leading_with(start, m.end(), chunk)
        pos = (start, m.end())
        if pos not in used:
            used.add(pos)
            result.append(pos)
    return result


async def process_chunk(
    chunk_text: str, offset: int, prompt_path: Path, chatbot: ChatBot
) -> list[CharacteristicDetection]:
    prompt_text = render_prompt(str(prompt_path), chunk_text)
    response = await chatbot.structured_chat([{"role": "user", "content": prompt_text}], CharacteristicExtractionOutput)

    used_positions: set[tuple[int, int]] = set()
    for item in response.detected_characteristics:
        new_spans: list[TextSpan] = []
        for span in item.evidence_spans:
            original_text = span.text.strip()
            positions = _find_new_positions(original_text, chunk_text, used_positions)
            if not positions:
                span.start_index = None
                span.end_index = None
                continue
            first_start, first_end = positions[0]
            span.start_index = first_start + offset
            span.end_index = first_end + offset
            span.text = chunk_text[first_start:first_end]
            if len(original_text) >= _MIN_MULTI_OCCURRENCE_LEN:
                new_spans.extend(
                    TextSpan(text=chunk_text[s:e], start_index=s + offset, end_index=e + offset)
                    for s, e in positions[1:]
                )
        item.evidence_spans.extend(new_spans)
    return response.detected_characteristics
