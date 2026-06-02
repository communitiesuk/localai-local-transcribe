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


_ARTICLE_PREFIX_RE = re.compile(r"(?<!\w)(an|a|the|my|our) $", re.IGNORECASE)


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


def deduplicate_characteristics(characteristics: list[CharacteristicDetection]) -> list[CharacteristicDetection]:
    """Merges characteristics with the same category and value, combining their evidence spans."""
    merged: dict[str, CharacteristicDetection] = {}

    for item in characteristics:
        category = item.characteristic
        value = item.attribute_value
        signature = f"{category}|{value}"

        if signature in merged:
            seen_positions = {(s.start_index, s.end_index) for s in merged[signature].evidence_spans}
            for span in item.evidence_spans:
                pos = (span.start_index, span.end_index)
                if pos not in seen_positions:
                    merged[signature].evidence_spans.append(span)
                    seen_positions.add(pos)
        else:
            merged[signature] = item

    return list(merged.values())


def build_chunks(transcript: str, chunk_size_chars: int = 1000, overlap_chars: int = 250) -> list[tuple[str, int]]:
    stride = chunk_size_chars - overlap_chars
    chunks = []
    start = 0
    while start < len(transcript):
        chunks.append((transcript[start : start + chunk_size_chars], start))
        start += stride
    return chunks


async def process_chunk(
    chunk_text: str, offset: int, prompt_path: Path, chatbot: ChatBot
) -> list[CharacteristicDetection]:
    prompt_text = render_prompt(str(prompt_path), chunk_text)
    response = await chatbot.structured_chat([{"role": "user", "content": prompt_text}], CharacteristicExtractionOutput)

    used_positions: set[tuple[int, int]] = set()
    for item in response.detected_characteristics:
        extra_spans: list[tuple[str, int, int]] = []  # (text, start_index, end_index) for additional occurrences
        for span in item.evidence_spans:
            original_text = span.text.strip()
            pattern = re.escape(original_text)
            span_assigned = False
            for match in re.finditer(pattern, chunk_text):
                start = _article_extended_start(match.start(), chunk_text)
                pos = (start, match.end())
                if pos in used_positions:
                    continue
                used_positions.add(pos)
                span_text = chunk_text[start : match.end()]
                if not span_assigned:
                    span.start_index = start + offset
                    span.end_index = match.end() + offset
                    span.text = span_text
                    span_assigned = True
                elif len(original_text) >= _MIN_MULTI_OCCURRENCE_LEN:
                    extra_spans.append((span_text, start + offset, match.end() + offset))
            if not span_assigned:
                span.start_index = None
                span.end_index = None

        item.evidence_spans.extend(TextSpan(text=t, start_index=s, end_index=e) for t, s, e in extra_spans)
    return response.detected_characteristics
