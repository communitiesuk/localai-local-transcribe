from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.summarisation.src.optimisation.data.loader import (
    discover_transcript_files,
    load_local_examples,
    load_transcript_json,
)


def _write_transcript(path: Path, entries: list[dict[str, object]], **extra: object) -> Path:
    payload: dict[str, object] = {
        "theme": "A tenant reports a repair",
        "word_target": 1200,
        "num_speakers": 2,
        "actor_definitions": ["I am a housing officer.", "I am a tenant."],
        "dialogue_entries": entries,
        **extra,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


_ENTRIES = [
    {"speaker": "1", "text": "Hello, how can I help?", "start_time": 0.0, "end_time": 1.0},
    {"speaker": "2", "text": "My tap is dripping.", "start_time": 1.0, "end_time": 2.0},
]


def test_load_transcript_json_reads_dialogue_entries(tmp_path):
    path = _write_transcript(tmp_path / "call.json", _ENTRIES)

    transcript = load_transcript_json(path)

    assert len(transcript.dialogue_entries) == 2
    assert transcript.dialogue_entries[0]["speaker"] == "1"
    assert transcript.dialogue_entries[1]["text"] == "My tap is dripping."
    assert transcript.theme == "A tenant reports a repair"


def test_load_transcript_json_ignores_generator_bookkeeping(tmp_path):
    path = _write_transcript(tmp_path / "call.json", _ENTRIES, some_future_field="ignored")

    transcript = load_transcript_json(path)

    assert transcript.num_speakers == 2


def test_load_transcript_json_rejects_missing_dialogue_entries(tmp_path):
    path = tmp_path / "call.json"
    path.write_text(json.dumps({"theme": "no entries"}), encoding="utf-8")

    with pytest.raises(ValueError, match="dialogue_entries"):
        load_transcript_json(path)


def test_discover_transcript_files_is_sorted(tmp_path):
    for name in ("c.json", "a.json", "b.json"):
        _write_transcript(tmp_path / name, _ENTRIES)

    files = discover_transcript_files(tmp_path)

    assert [f.name for f in files] == ["a.json", "b.json", "c.json"]


def test_discover_transcript_files_missing_dir_raises(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        discover_transcript_files(tmp_path / "absent")


def test_discover_transcript_files_empty_dir_raises(tmp_path):
    with pytest.raises(ValueError, match="No JSON files found"):
        discover_transcript_files(tmp_path)


def test_load_local_examples_uses_filename_as_example_id(tmp_path):
    _write_transcript(tmp_path / "relational_listening_ear_call.json", _ENTRIES)

    examples = load_local_examples(tmp_path)

    assert [ex.example_id for ex in examples] == ["relational_listening_ear_call"]


def test_load_local_examples_carries_entries_and_numbers_dialogue(tmp_path):
    _write_transcript(tmp_path / "call.json", _ENTRIES)

    example = load_local_examples(tmp_path)[0]

    assert example.dialogue_entries == _ENTRIES
    assert example.dialogue.startswith("[0] ")
    assert "My tap is dripping." in example.dialogue
    # The generated transcripts carry no gold summary; the rubric judge is reference-free.
    assert example.reference_summary is None


def test_load_local_examples_preserves_multiline_utterances(tmp_path):
    entries = [{"speaker": "1", "text": "First thought.\nSecond thought.", "start_time": 0.0, "end_time": 1.0}]
    _write_transcript(tmp_path / "call.json", entries)

    example = load_local_examples(tmp_path)[0]

    assert len(example.dialogue_entries) == 1
    assert example.dialogue_entries[0]["text"] == "First thought.\nSecond thought."


def test_load_local_examples_applies_limit(tmp_path):
    for name in ("a.json", "b.json", "c.json"):
        _write_transcript(tmp_path / name, _ENTRIES)

    examples = load_local_examples(tmp_path, limit=2)

    assert [ex.example_id for ex in examples] == ["a", "b"]
