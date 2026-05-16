from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from evals.summarisation.src.bias.bias_types import CounterfactualInput
from evals.summarisation.src.bias.data.loader import discover_counterfactual_files, load_counterfactual_json


@pytest.fixture
def sample_counterfactual_data():
    return {
        "original_transcript": {
            "dialogue_entries": [
                {"speaker": "1", "text": "Hello there", "start_time": 0.0, "end_time": 1.0},
                {"speaker": "2", "text": "Hi back", "start_time": 1.0, "end_time": 2.0},
            ],
            "metadata": {"source": "test"},
        },
        "rewritten_transcript": [
            {"speaker": "1", "text": "Hello there", "start_time": 0.0, "end_time": 1.0},
            {"speaker": "2", "text": "Hi back", "start_time": 1.0, "end_time": 2.0},
        ],
        "axis_change": {
            "axis": "gender",
            "original_value": "male",
            "target_value": "female",
            "instructions": "Change male to female",
        },
        "model_version": "gpt-4",
        "prompt_version": "v1",
        "evidence_spans_modified": [0, 1],
    }


def test_load_counterfactual_json_valid(tmp_path, sample_counterfactual_data):
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(sample_counterfactual_data), encoding="utf-8")

    result = load_counterfactual_json(json_file)

    assert isinstance(result, CounterfactualInput)
    assert result.protected_characteristic == "gender"
    assert result.axis_of_change == "male_to_female"
    assert len(result.original_dialogue_entries) == 2
    assert len(result.counterfactual_dialogue_entries) == 2
    assert result.original_dialogue_entries[0]["speaker"] == "1"
    assert result.original_dialogue_entries[0]["text"] == "Hello there"
    assert result.axis_change.axis == "gender"
    assert result.axis_change.original_value == "male"
    assert result.axis_change.target_value == "female"


def test_load_counterfactual_json_properties(tmp_path, sample_counterfactual_data):
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(sample_counterfactual_data), encoding="utf-8")

    result = load_counterfactual_json(json_file)

    assert result.variant_id == "gender_male_to_female"
    assert result.model_version == "gpt-4"
    assert result.prompt_version == "v1"
    assert len(result.evidence_spans_modified) == 2
    assert result.evidence_spans_modified == [0, 1]
    assert result.original_transcript.metadata["source"] == "test"


def test_load_counterfactual_json_invalid_data(tmp_path):
    json_file = tmp_path / "invalid.json"
    json_file.write_text('{"invalid": "data"}', encoding="utf-8")

    with pytest.raises(ValidationError):
        load_counterfactual_json(json_file)


def test_discover_counterfactual_files_single_file(tmp_path, sample_counterfactual_data):
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(sample_counterfactual_data), encoding="utf-8")

    files = discover_counterfactual_files(tmp_path)

    assert len(files) == 1
    assert files[0] == json_file
    assert files[0].name == "test.json"
    assert files[0].exists()


def test_discover_counterfactual_files_multiple_files(tmp_path, sample_counterfactual_data):
    for i in range(3):
        json_file = tmp_path / f"test_{i}.json"
        json_file.write_text(json.dumps(sample_counterfactual_data), encoding="utf-8")

    files = discover_counterfactual_files(tmp_path)

    assert len(files) == 3
    file_names = {f.name for f in files}
    assert file_names == {"test_0.json", "test_1.json", "test_2.json"}
    assert all(f.suffix == ".json" for f in files)


def test_discover_counterfactual_files_nested_directories(tmp_path, sample_counterfactual_data):
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    json_file1 = tmp_path / "test1.json"
    json_file1.write_text(json.dumps(sample_counterfactual_data), encoding="utf-8")

    json_file2 = subdir / "test2.json"
    json_file2.write_text(json.dumps(sample_counterfactual_data), encoding="utf-8")

    files = discover_counterfactual_files(tmp_path)

    assert len(files) == 2
    file_names = {f.name for f in files}
    assert file_names == {"test1.json", "test2.json"}
    assert any("subdir" in str(f) for f in files)


def test_discover_counterfactual_files_no_json_files(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match="No JSON files found"):
        discover_counterfactual_files(tmp_path)


def test_discover_counterfactual_files_nonexistent_directory(tmp_path):
    nonexistent = tmp_path / "does_not_exist"

    with pytest.raises(ValueError, match="Input directory does not exist"):
        discover_counterfactual_files(nonexistent)


def test_discover_counterfactual_files_ignores_non_json(tmp_path, sample_counterfactual_data):
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(sample_counterfactual_data), encoding="utf-8")

    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not json", encoding="utf-8")

    py_file = tmp_path / "test.py"
    py_file.write_text("print('hello')", encoding="utf-8")

    files = discover_counterfactual_files(tmp_path)

    assert len(files) == 1
    assert files[0].suffix == ".json"
    assert files[0].name == "test.json"
    assert txt_file.exists()
    assert py_file.exists()
