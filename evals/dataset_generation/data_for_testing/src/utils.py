import json
import logging
from pathlib import Path

from evals.characteristics.src.transcript_loader import load_transcript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_span_indices(transcript_path: Path, search_text: str) -> list[dict]:
    """Finds all occurrences of a text span and return their indices."""
    if not search_text:
        error_msg = "search_text cannot be empty"
        raise ValueError(error_msg)

    transcript = load_transcript(transcript_path)
    results = []
    start = 0
    while True:
        idx = transcript.find(search_text, start)
        if idx == -1:
            break
        results.append({"text": search_text, "start_index": idx, "end_index": idx + len(search_text)})
        start = idx + 1
    return results


def write_span_indices(span_indices: list[dict], output_path: Path) -> None:
    output_path.write_text(json.dumps(span_indices, indent=2), encoding="utf-8")
    logger.info("Wrote %d spans to %s", len(span_indices), output_path)
