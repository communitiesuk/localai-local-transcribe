import json

import pytest

from evals.dataset_generation.counterfactual_generation.src.main import _load_transcript

DIALOGUE_ENTRIES = [
    {"speaker": "Officer", "text": "Thanks for calling", "start_time": 0.0, "end_time": 1.0},
    {"speaker": "Tenant", "text": "No problem", "start_time": 1.0, "end_time": 2.0},
]


def _write_transcript(tmp_path, payload, name="my_transcript.json"):
    """Write a transcript file and return its path."""
    transcript_path = tmp_path / name
    transcript_path.write_text(json.dumps(payload))
    return transcript_path


def test_metadata_names_the_source_transcript(tmp_path):
    transcript_path = _write_transcript(tmp_path, {"dialogue_entries": DIALOGUE_ENTRIES})

    transcript_input = _load_transcript(transcript_path)

    assert transcript_input.metadata["source_transcript_id"] == "my_transcript"
    assert transcript_input.metadata["source_transcript_path"] == str(transcript_path)


def test_metadata_keeps_generation_details_from_the_transcript_file(tmp_path):
    transcript_path = _write_transcript(
        tmp_path,
        {
            "theme": "A tenant asks about a repair",
            "num_speakers": 2,
            "actor_definitions": ["I am the housing officer"],
            "dialogue_entries": DIALOGUE_ENTRIES,
        },
    )

    transcript_input = _load_transcript(transcript_path)

    assert transcript_input.metadata["theme"] == "A tenant asks about a repair"
    assert transcript_input.metadata["num_speakers"] == 2
    assert transcript_input.metadata["actor_definitions"] == ["I am the housing officer"]
    # The dialogue is returned in its own field, so repeating it inside the metadata would only
    # double the size of every counterfactual file.
    assert "dialogue_entries" not in transcript_input.metadata


def test_dialogue_is_returned_alongside_the_metadata(tmp_path):
    transcript_path = _write_transcript(tmp_path, {"dialogue_entries": DIALOGUE_ENTRIES})

    transcript_input = _load_transcript(transcript_path)

    assert len(transcript_input.dialogue_entries) == 2
    assert transcript_input.dialogue_entries[0]["text"] == "Thanks for calling"


def test_transcript_stored_as_a_bare_list_still_gets_identifiers(tmp_path):
    transcript_path = _write_transcript(tmp_path, DIALOGUE_ENTRIES)

    transcript_input = _load_transcript(transcript_path)

    assert transcript_input.metadata == {
        "source_transcript_id": "my_transcript",
        "source_transcript_path": str(transcript_path),
    }


def test_transcript_without_dialogue_raises(tmp_path):
    transcript_path = _write_transcript(tmp_path, {"dialogue_entries": []})

    with pytest.raises(ValueError, match="No dialogue_entries found"):
        _load_transcript(transcript_path)
