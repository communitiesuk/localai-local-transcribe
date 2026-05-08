import re
from pathlib import Path

from common.llm.client import ChatBot
from evals.dataset_generation.characteristics.src.config_loader import render_prompt
from evals.dataset_generation.characteristics.src.schema import (
    CharacteristicDetection,
    CharacteristicExtractionOutput,
)


def find_spans(text: str, transcript: str) -> list[tuple[int, int]]:
    """Find all occurrences of text in transcript, returning (start, end) index tuples."""
    pattern = re.escape(text.strip())
    return [(m.start(), m.end()) for m in re.finditer(pattern, transcript)]


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

    used_positions = set()
    for item in response.detected_characteristics:
        for span in item.evidence_spans:
            pattern = re.escape(span.text.strip())
            matched = False
            for match in re.finditer(pattern, chunk_text):
                pos = (match.start(), match.end())
                if pos not in used_positions:
                    span.start_index = match.start() + offset
                    span.end_index = match.end() + offset
                    span.text = match.group()
                    used_positions.add(pos)
                    matched = True
                    break
            if not matched:
                span.start_index = None
                span.end_index = None
    return response.detected_characteristics
