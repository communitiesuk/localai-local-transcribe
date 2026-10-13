from __future__ import annotations

import json

import pytest

from evals.transcription.src.core.ami.metadata import load_or_build_metadata


def test_metadata_forwards_configured_arrow_cache_directory(tmp_path, monkeypatch):
    """Metadata loading forwards the datasets Arrow cache directory."""
    captured = {}

    def fake_load_dataset(_name, _config, split, cache_dir):  # noqa: ARG001
        captured["cache_dir"] = cache_dir
        return []

    monkeypatch.setattr("evals.transcription.src.core.ami.metadata.load_dataset", fake_load_dataset)

    with pytest.raises(RuntimeError, match="No meetings found in AMI ihm/test"):
        load_or_build_metadata(tmp_path, "test", "ihm", tmp_path / "raw")

    assert captured["cache_dir"] == str(tmp_path / "raw")


@pytest.mark.parametrize("existing_empty_cache", [False, True])
def test_empty_metadata_fetch_can_be_retried(tmp_path, monkeypatch, existing_empty_cache):
    metadata_path = tmp_path / "meeting_metadata.json"
    if existing_empty_cache:
        metadata_path.write_text(json.dumps({"meeting_ids": [], "durations_sec": {}}), encoding="utf-8")
    fetches = iter([[], [{"meeting_id": "meeting", "end_time": 3.0}]])
    monkeypatch.setattr(
        "evals.transcription.src.core.ami.metadata.load_dataset", lambda *_args, **_kwargs: next(fetches)
    )
    with pytest.raises(RuntimeError, match="No meetings found in AMI"):
        load_or_build_metadata(tmp_path)
    if not existing_empty_cache:
        assert not metadata_path.exists()
    assert load_or_build_metadata(tmp_path).meeting_ids == ["meeting"]
    assert json.loads(metadata_path.read_text())["meeting_ids"] == ["meeting"]


@pytest.mark.parametrize("download_dir_name", [None, "raw"])
def test_empty_metadata_error_does_not_claim_a_download_location(tmp_path, monkeypatch, download_dir_name):
    monkeypatch.setattr("evals.transcription.src.core.ami.metadata.load_dataset", lambda *_args, **_kwargs: [])
    download_dir = tmp_path / download_dir_name if download_dir_name else None
    with pytest.raises(RuntimeError) as error:
        load_or_build_metadata(tmp_path, download_dir=download_dir)
    assert "No meetings found" in str(error.value)
    assert "None" not in str(error.value)
    assert "download in" not in str(error.value)
