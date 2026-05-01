import json
import logging
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TranscriptTurn(BaseModel):
    """Represents a single turn in a conversation transcript."""

    speaker: str
    text: str


def load_transcript(file_path: Path) -> str:
    """Loads and formats transcript from a file (.txt or .json)."""
    if file_path.suffix == ".txt":
        return file_path.read_text(encoding="utf-8")

    if file_path.suffix == ".json":
        raw_data = json.loads(file_path.read_text(encoding="utf-8"))

        if isinstance(raw_data, dict) and "dialogue_entries" in raw_data:
            dialogue_entries = raw_data["dialogue_entries"]
        else:
            dialogue_entries = raw_data

        turns = [TranscriptTurn(**item) for item in dialogue_entries]
        return "\n".join(f"{t.speaker}: {t.text}" for t in turns)

    message = f"Unsupported format: {file_path.suffix}"
    logger.error(message)
    raise ValueError(message)
