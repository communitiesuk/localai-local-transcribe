from __future__ import annotations

import json
import shutil

import httpx
import pytest
from tenacity import Future, RetryError

from evals.dataset_generation.silver_transcripts.src.models import MeetingMetadata
from tests.evals.dataset_generation.silver_transcripts.support import result_factory


def _exhausted_retry(cause: BaseException, attempts: int = 5) -> RetryError:
    """Build what tenacity raises once a retrying call has spent all of its attempts."""
    attempt = Future(attempts)
    attempt.set_exception(cause)
    return RetryError(attempt)


def _only_failure(records: list[MeetingMetadata]) -> MeetingMetadata:
    failures = [record for record in records if record.status == "failed"]
    assert len(failures) == 1
    return failures[0]


def test_exhausted_service_retries_are_recorded_and_the_batch_continues(draft_setup, monkeypatch):
    input_dir, pipeline, adapter = draft_setup
    shutil.copyfile(input_dir / "sample.wav", input_dir / "broken.wav")

    def transcribe(wav_path: str):
        if "/broken-" in wav_path:
            raise _exhausted_retry(httpx.ConnectError("azure is unreachable"))
        return result_factory()

    monkeypatch.setattr(adapter, "transcribe", transcribe)
    records = pipeline.generate_transcripts(input_dir)

    assert {record.source_audio: record.status for record in records} == {
        "broken.wav": "failed",
        "sample.wav": "completed",
    }
    failed = _only_failure(records)
    assert failed.error.startswith("RetryError[")
    saved = json.loads((pipeline.work_dir / "drafts" / failed.sample_id / "metadata.json").read_text())
    assert saved["error"] == failed.error


@pytest.mark.parametrize("cause", [TypeError("unexpected type"), KeyError("missing"), ZeroDivisionError("nope")])
def test_an_unlisted_service_error_is_recorded_and_the_batch_continues(draft_setup, monkeypatch, cause):
    input_dir, pipeline, adapter = draft_setup
    shutil.copyfile(input_dir / "sample.wav", input_dir / "broken.wav")

    def transcribe(wav_path: str):
        if "/broken-" in wav_path:
            raise cause
        return result_factory()

    monkeypatch.setattr(adapter, "transcribe", transcribe)
    records = pipeline.generate_transcripts(input_dir)

    assert {record.source_audio: record.status for record in records} == {
        "broken.wav": "failed",
        "sample.wav": "completed",
    }
    assert _only_failure(records).error


@pytest.mark.parametrize("status", ["pending_review", "approved"])
def test_a_status_from_an_earlier_version_fails_only_its_own_sample(draft_setup, status):
    input_dir, pipeline, adapter = draft_setup
    first = pipeline.generate_transcripts(input_dir)
    path = pipeline.work_dir / "drafts" / first[0].sample_id / "metadata.json"
    path.write_text(json.dumps(json.loads(path.read_text()) | {"status": status}), encoding="utf-8")
    original_bytes = path.read_bytes()
    shutil.copyfile(input_dir / "sample.wav", input_dir / "later.wav")

    records = pipeline.generate_transcripts(input_dir)

    assert {record.source_audio: record.status for record in records} == {
        "sample.wav": "failed",
        "later.wav": "completed",
    }
    assert path.read_bytes() == original_bytes
    assert "status" in _only_failure(records).error
    assert adapter.calls == 2


@pytest.mark.parametrize("content", ["not json at all", "", '{"status": "completed"}'])
def test_unreadable_draft_metadata_fails_only_its_own_sample(draft_setup, content):
    input_dir, pipeline, adapter = draft_setup
    first = pipeline.generate_transcripts(input_dir)
    path = pipeline.work_dir / "drafts" / first[0].sample_id / "metadata.json"
    path.write_text(content, encoding="utf-8")
    shutil.copyfile(input_dir / "sample.wav", input_dir / "later.wav")

    records = pipeline.generate_transcripts(input_dir)

    assert {record.source_audio: record.status for record in records} == {
        "sample.wav": "failed",
        "later.wav": "completed",
    }
    assert path.read_text() == content
    assert _only_failure(records).error
    assert adapter.calls == 2


@pytest.mark.parametrize(
    "disturbance",
    ["segments_moved_away", "segment_folder_gone", "audio_gone", "transcript_gone", "segment_metadata_corrupt"],
)
def test_completed_drafts_resume_quietly_once_segments_have_moved_on(draft_setup, disturbance):
    input_dir, pipeline, adapter = draft_setup
    original = pipeline.generate_transcripts(input_dir)
    segments = pipeline.work_dir / "drafts" / original[0].sample_id / "segments"
    folder = segments / "segment_0000"
    if disturbance == "segments_moved_away":
        shutil.rmtree(segments)
    elif disturbance == "segment_folder_gone":
        shutil.rmtree(folder)
    elif disturbance == "audio_gone":
        (folder / "audio.mp3").unlink()
    elif disturbance == "transcript_gone":
        (folder / "audio.txt").unlink()
    else:
        (folder / "metadata.json").write_text('{"unexpected": true}', encoding="utf-8")

    assert pipeline.generate_transcripts(input_dir) == original
    assert adapter.calls == 1


def test_resume_does_not_check_the_recorded_segment_count(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    original = pipeline.generate_transcripts(input_dir)
    path = pipeline.work_dir / "drafts" / original[0].sample_id / "metadata.json"
    metadata = json.loads(path.read_text()) | {"segment_count": 2}
    path.write_text(json.dumps(metadata), encoding="utf-8")

    assert pipeline.generate_transcripts(input_dir)[0].segment_count == 2
    assert adapter.calls == 1


def test_resume_returns_validated_metadata(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    original = pipeline.generate_transcripts(input_dir)
    path = pipeline.work_dir / "drafts" / original[0].sample_id / "metadata.json"
    saved = json.loads(path.read_text())
    saved["segment_count"] = "1"
    saved["obsolete_field"] = "discard"
    path.write_text(json.dumps(saved))
    assert pipeline.generate_transcripts(input_dir) == original
    assert adapter.calls == 1
