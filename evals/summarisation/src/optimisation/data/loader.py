from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from common.database.postgres_models import DialogueEntry
from evals.summarisation.src.common.schemas import DialogExample
from evals.summarisation.src.transcript import judge_transcript_text


class GeneratedTranscript(BaseModel):
    """A synthetic transcript as written by ``evals/dataset_generation/transcription_generation``."""

    dialogue_entries: list[DialogueEntry]
    theme: str | None = None
    num_speakers: int | None = None


def load_transcript_json(file_path: Path) -> GeneratedTranscript:
    """Loads and validates a single generated transcript from a JSON file."""
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return GeneratedTranscript.model_validate(data)


def discover_transcript_files(input_dir: Path) -> list[Path]:
    """Discovers all JSON transcript files in the input directory (sorted for determinism)."""
    if not input_dir.exists():
        msg = f"Input directory does not exist: {input_dir}"
        raise ValueError(msg)

    json_files = sorted(input_dir.glob("**/*.json"))
    if not json_files:
        msg = f"No JSON files found in {input_dir}"
        raise ValueError(msg)

    return json_files


def load_local_examples(input_dir: Path, limit: int | None = None) -> list[DialogExample]:
    """Loads every generated transcript in ``input_dir`` as a standard-eval example.

    Entries are carried through as-is; a generated utterance can span several lines, so recovering
    entries by splitting text would fragment one turn and misattribute its tail. The filename is the
    example id.
    """
    files = discover_transcript_files(input_dir)
    if limit is not None:
        files = files[:limit]

    return [
        DialogExample(
            example_id=path.stem,
            dialogue=judge_transcript_text(transcript.dialogue_entries),
            dialogue_entries=transcript.dialogue_entries,
            reference_summary=None,
        )
        for path, transcript in ((p, load_transcript_json(p)) for p in files)
    ]
