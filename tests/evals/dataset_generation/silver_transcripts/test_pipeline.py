from __future__ import annotations

import asyncio
import json
import shutil
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

import httpx
import numpy as np
import pytest
import soundfile
from ffmpeg import Error as FFmpegError
from tenacity import Future, RetryError

from common.audio.ffmpeg import convert_to_mp3
from common.services.transcription_services.azure_stt_base import convert_to_dialogue_entries
from evals.dataset_generation.silver_transcripts.src import pipeline as pipeline_module
from evals.dataset_generation.silver_transcripts.src.main import main
from evals.dataset_generation.silver_transcripts.src.models import MeetingMetadata
from evals.dataset_generation.silver_transcripts.src.pipeline import (
    MAX_SAMPLE_NAME_LENGTH,
    MAX_SEGMENT_SPAN_FACTOR,
    SilverTranscriptPipeline,
)
from evals.transcription.src.adapters.base import EvalsTranscriptionAdapter
from evals.transcription.src.models import TranscriptionResult

DRAFT_TEXT = "the original draft"


def _result(text: str = DRAFT_TEXT, **overrides) -> TranscriptionResult:
    entries = [{"speaker": "1", "text": text, "start_time": 0.0, "end_time": 1.0}]
    return TranscriptionResult(
        **{"text": text, "duration_sec": 0.25, "debug_info": {}, "dialogue_entries": entries, **overrides}
    )


class DraftAdapter(EvalsTranscriptionAdapter):
    def __init__(self, fail: bool = False):
        self.calls = 0
        self.fail = fail

    @property
    def name(self) -> str:
        return "test_engine"

    def transcribe(self, wav_path: str) -> TranscriptionResult:
        assert Path(wav_path).is_file()
        self.calls += 1
        if self.fail:
            return _result("", debug_info={"error": "service failed"})
        return _result()


def _copy_cut(source, destination, _start, _end) -> None:
    """Stand in for cut_audio so segment logic can be tested without ffmpeg."""
    shutil.copyfile(source, destination)


_REAL_CUT_AUDIO = SilverTranscriptPipeline.cut_audio


@pytest.fixture
def draft_setup(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    soundfile.write(input_dir / "sample.wav", np.zeros(16000), 16000)
    monkeypatch.setattr("evals.dataset_generation.silver_transcripts.src.pipeline.convert_to_mp3", shutil.copyfile)
    adapter = DraftAdapter()
    pipeline = SilverTranscriptPipeline(tmp_path / "work", adapter)
    # Patched on the class, not the instance, so it also covers the pipeline main() builds itself.
    # Tests that exercise real encoding restore it and skip when ffmpeg is absent.
    monkeypatch.setattr(SilverTranscriptPipeline, "cut_audio", staticmethod(_copy_cut))
    return input_dir, pipeline, adapter


def test_generation_writes_segment_files(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    records = pipeline.generate_transcripts(input_dir)
    sample_id = records[0].sample_id
    folder = pipeline.work_dir / "drafts" / sample_id / "segments" / "segment_0000"
    assert records[0].status == "completed"
    assert records[0].engine == "test_engine"
    meeting_dir = pipeline.work_dir / "drafts" / sample_id
    assert not (meeting_dir / "audio.txt").exists()
    assert (meeting_dir / "draft.txt").read_text() == "Speaker 1: the original draft\n"
    (folder / "audio.txt").write_text("the corrected reference", encoding="utf-8")
    assert (folder / "audio.txt").read_text() == "the corrected reference"
    provenance = json.loads((folder / "metadata.json").read_text())
    assert provenance["status"] == "completed"
    assert not {"standard", "source_sha256", "audio_sha256", "draft_sha256", "dialogue_entries"} & provenance.keys()
    assert not (folder / "draft.txt").exists()
    assert adapter.calls == 1


def test_rerunning_generation_preserves_review_edits(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    first = pipeline.generate_transcripts(input_dir)
    transcript = pipeline.work_dir / "drafts" / first[0].sample_id / "segments" / "segment_0000" / "audio.txt"
    transcript.write_text("review edits", encoding="utf-8")
    assert pipeline.generate_transcripts(input_dir) == first
    assert transcript.read_text() == "review edits"
    assert adapter.calls == 1


def test_changed_source_requires_explicit_regeneration(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    first = pipeline.generate_transcripts(input_dir)
    soundfile.write(input_dir / "sample.wav", np.ones(16000) * 0.1, 16000)
    assert pipeline.generate_transcripts(input_dir) == first
    assert adapter.calls == 1


def test_failed_transcription_is_recorded_and_retried(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    adapter.fail = True
    failed = pipeline.generate_transcripts(input_dir)[0]
    assert failed.status == "failed"
    assert failed.error == "service failed"
    assert not list((pipeline.work_dir / "drafts").glob("*/segments/*/audio.mp3"))
    adapter.fail = False
    assert pipeline.generate_transcripts(input_dir)[0].status == "completed"


def test_same_stem_in_different_directories_produces_distinct_pairs(draft_setup):
    input_dir, pipeline, _adapter = draft_setup
    subdir = input_dir / "other"
    subdir.mkdir()
    shutil.copyfile(input_dir / "sample.wav", subdir / "sample.wav")
    records = pipeline.generate_transcripts(input_dir)
    assert len({record.sample_id for record in records}) == 2


def test_real_ffmpeg_generates_playable_audio_for_review(draft_setup, monkeypatch):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg and ffprobe are required")
    input_dir, pipeline, adapter = draft_setup
    soundfile.write(input_dir / "sample.wav", np.zeros((16000, 2)), 16000)
    monkeypatch.setattr("evals.dataset_generation.silver_transcripts.src.pipeline.convert_to_mp3", convert_to_mp3)
    monkeypatch.setattr(SilverTranscriptPipeline, "cut_audio", staticmethod(_REAL_CUT_AUDIO))
    sample_id = pipeline.generate_transcripts(input_dir)[0].sample_id
    audio, sample_rate = soundfile.read(pipeline.work_dir / "drafts" / sample_id / "audio.mp3")
    assert sample_rate == 16000
    assert len(audio) == 16000
    assert audio.ndim == 1
    assert adapter.calls == 1


def test_failed_conversion_is_recorded_without_calling_the_service(draft_setup, monkeypatch):
    input_dir, pipeline, adapter = draft_setup

    def fail_conversion(_source, _target):
        command = "ffmpeg"
        raise FFmpegError(command, b"", b"invalid input")

    monkeypatch.setattr("evals.dataset_generation.silver_transcripts.src.pipeline.convert_to_mp3", fail_conversion)
    record = pipeline.generate_transcripts(input_dir)[0]
    assert record.status == "failed"
    assert "ffmpeg" in record.error
    assert adapter.calls == 0


def test_output_inside_input_is_rejected_before_service_calls(draft_setup):
    input_dir, _pipeline, adapter = draft_setup
    pipeline = SilverTranscriptPipeline(input_dir / "generated", adapter)
    with pytest.raises(ValueError, match="outside input_dir"):
        pipeline.generate_transcripts(input_dir)
    assert adapter.calls == 0


@pytest.mark.parametrize("cutoff", [0, -1, float("inf"), float("nan")])
def test_pipeline_rejects_an_invalid_cutoff(tmp_path, cutoff):
    with pytest.raises(ValueError, match="cutoff_seconds must be finite"):
        SilverTranscriptPipeline(tmp_path / "work", cutoff_seconds=cutoff)


def test_missing_input_dir_is_rejected_before_service_calls(draft_setup, tmp_path):
    _input_dir, pipeline, adapter = draft_setup
    with pytest.raises(NotADirectoryError):
        pipeline.generate_transcripts(tmp_path / "absent")
    assert adapter.calls == 0


def test_unsupported_files_are_not_discovered_as_input(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    (input_dir / "notes.txt").write_text("not audio", encoding="utf-8")
    (input_dir / "clip.mov").write_bytes(b"not audio")
    records = pipeline.generate_transcripts(input_dir)
    assert [record.source_audio for record in records] == ["sample.wav"]
    assert adapter.calls == 1


def test_input_dir_without_supported_audio_is_rejected(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    (input_dir / "sample.wav").unlink()
    (input_dir / "notes.txt").write_text("not audio", encoding="utf-8")
    with pytest.raises(ValueError, match="No supported audio files found"):
        pipeline.generate_transcripts(input_dir)
    assert adapter.calls == 0


def test_sample_ids_are_sanitised_and_truncated(draft_setup):
    input_dir, pipeline, _adapter = draft_setup
    (input_dir / "sample.wav").rename(input_dir / f"my meeting (final) {'x' * 80}.wav")
    record = pipeline.generate_transcripts(input_dir)[0]
    name, _, identity = record.sample_id.rpartition("-")
    assert name == f"my_meeting__final__{'x' * 80}"[:MAX_SAMPLE_NAME_LENGTH]
    assert len(name) == MAX_SAMPLE_NAME_LENGTH
    assert len(identity) == 16


def test_sample_id_falls_back_when_the_stem_sanitises_to_nothing():
    assert SilverTranscriptPipeline._sample_id("meetings/.wav", "").startswith("audio-")  # noqa: SLF001


@pytest.mark.parametrize(
    ("confidences", "expected_mean", "expected_std"),
    [([0.6, 1.0, None], 0.8, 0.2), ([0.7], 0.7, 0.0), ([None], None, None)],
)
def test_utterance_segments_and_confidence_metadata(draft_setup, monkeypatch, confidences, expected_mean, expected_std):
    input_dir, pipeline, adapter = draft_setup
    soundfile.write(input_dir / "sample.wav", np.zeros(16000 * len(confidences)), 16000)
    phrases = [
        {
            "speaker": 1,
            "text": "hello",
            "offsetMilliseconds": index * 1000,
            "durationMilliseconds": 1000,
            "confidence": confidence,
        }
        for index, confidence in enumerate(confidences)
    ]
    utterances = convert_to_dialogue_entries(phrases)
    monkeypatch.setattr(
        adapter,
        "transcribe",
        lambda _path: _result(
            text=" ".join(entry["text"] for entry in utterances), duration_sec=1, dialogue_entries=utterances
        ),
    )
    record = pipeline.generate_transcripts(input_dir)[0]
    assert record.utterance_count == len(confidences)
    assert record.scored_utterance_count == sum(score is not None for score in confidences)
    for field, expected in (("mean_utterance_confidence", expected_mean), ("std_utterance_confidence", expected_std)):
        if expected is None:
            assert getattr(record, field) is None
        else:
            assert getattr(record, field) == pytest.approx(expected)
    # Utterance detail is summarised into the metadata statistics; it is not kept as its own file.
    draft_dir = pipeline.work_dir / "drafts" / record.sample_id
    assert not (draft_dir / "utterances.json").exists()
    assert not list((draft_dir / "segments").glob("*/utterances.json"))


@pytest.mark.parametrize(
    ("times", "expected"),
    [
        ([(0, 300), (300, 600), (600, 610)], [2, 1]),
        ([(0, 590), (589, 620), (620, 630)], [2, 1]),
        ([(0, 700), (700, 710)], [1, 1]),
        ([(0, 1), (900, 901)], [1, 1]),
    ],
)
def test_groups_preserve_whole_utterances(times, expected):
    entries = [
        {"speaker": "1", "text": str(index), "start_time": start, "end_time": end}
        for index, (start, end) in enumerate(times)
    ]
    groups = SilverTranscriptPipeline.group_utterances(entries[::-1])
    assert [len(group) for group in groups] == expected
    assert [entry for group in groups for entry in group] == entries
    for left, right in pairwise(groups):
        assert max(entry["end_time"] for entry in left) <= right[0]["start_time"]


def test_continuous_overlap_is_still_split_into_bounded_segments():
    # 50% overlap throughout, so no boundary exists where speech stops; only the hard limit can split.
    entries = [
        {"speaker": "1", "text": str(index), "start_time": index * 10.0, "end_time": index * 10.0 + 20.0}
        for index in range(600)
    ]
    groups = SilverTranscriptPipeline.group_utterances(entries, 600.0)
    spans = [max(entry["end_time"] for entry in group) - group[0]["start_time"] for group in groups]
    assert len(groups) > 1
    assert max(spans) <= 600.0 * MAX_SEGMENT_SPAN_FACTOR
    assert [entry for group in groups for entry in group] == entries


def test_long_overlapping_utterance_does_not_suppress_later_splits():
    # The first utterance alone outruns the window; the quiet exchange after it must still split.
    entries = [
        {"speaker": "1", "text": "long", "start_time": 0.0, "end_time": 1300.0},
        {"speaker": "2", "text": "overlaps", "start_time": 1200.0, "end_time": 1400.0},
        {"speaker": "1", "text": "after", "start_time": 2100.0, "end_time": 2110.0},
    ]
    groups = SilverTranscriptPipeline.group_utterances(entries, 600.0)
    assert [len(group) for group in groups] == [1, 1, 1]
    assert [entry for group in groups for entry in group] == entries


@pytest.mark.parametrize(
    "interval",
    [(-1.0, 1.0), (1.0, 1.0), (2.0, 1.0), (float("nan"), 1.0), (0.0, float("inf")), (0.0, float("nan"))],
)
def test_group_utterances_rejects_invalid_intervals(interval):
    start, end = interval
    entries = [{"speaker": "1", "text": "x", "start_time": start, "end_time": end}]
    with pytest.raises(ValueError, match="non-negative start times"):
        SilverTranscriptPipeline.group_utterances(entries)


def test_group_utterances_requires_at_least_one_utterance():
    with pytest.raises(ValueError, match="Utterance timestamps are required"):
        SilverTranscriptPipeline.group_utterances([])


@pytest.mark.parametrize("leftover", ["no_metadata", "failed_metadata"])
def test_regeneration_replaces_segments_a_previous_run_left_behind(draft_setup, leftover):
    # Annotation happens on files moved out of the draft tree, so segments/ is regenerable
    # scratch. An interrupted run can publish it before metadata.json is written, and a later
    # failed run records "failed" while leaving it in place; both must regenerate cleanly.
    input_dir, pipeline, adapter = draft_setup
    draft_dir = pipeline.work_dir / "drafts" / pipeline.generate_transcripts(input_dir)[0].sample_id
    metadata_path = draft_dir / "metadata.json"
    if leftover == "no_metadata":
        metadata_path.unlink()
    else:
        metadata = json.loads(metadata_path.read_text()) | {"status": "failed"}
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    segments = draft_dir / "segments"
    (segments / "segment_0000" / "audio.txt").write_text("stale text", encoding="utf-8")
    (segments / "segment_0009").mkdir()

    record = pipeline.generate_transcripts(input_dir)[0]

    assert record.status == "completed"
    assert record.segment_count == 1
    # The stale folder from the longer previous run is gone, not merged into the new set.
    assert sorted(path.name for path in segments.iterdir()) == ["segment_0000"]
    assert (segments / "segment_0000" / "audio.txt").read_text() == "Speaker 1: the original draft\n"
    assert adapter.calls == 2


def test_real_audio_cut_preserves_interval(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg is required")
    source, output = tmp_path / "source.wav", tmp_path / "segment.mp3"
    audio = np.concatenate([np.zeros(16000), np.full(16000, 0.25), np.zeros(16000)])
    soundfile.write(source, audio, 16000)
    SilverTranscriptPipeline.cut_audio(source, output, 1.0, 2.0)
    decoded, rate = soundfile.read(output)
    assert rate == 16000
    assert len(decoded) == pytest.approx(16000, abs=1)
    assert np.mean(decoded[1000:-1000]) == pytest.approx(0.25, abs=0.02)


def test_missing_utterances_records_failed_generation(draft_setup, monkeypatch):
    input_dir, pipeline, adapter = draft_setup
    monkeypatch.setattr(
        adapter,
        "transcribe",
        lambda _path: _result(text="text without timestamps", duration_sec=1, dialogue_entries=[]),
    )
    assert pipeline.generate_transcripts(input_dir)[0].status == "failed"
    assert not list((pipeline.work_dir / "drafts").glob("*/segments/*/audio.mp3"))


def test_generation_writes_multiple_chunks_with_source_timestamps(draft_setup, monkeypatch):
    input_dir, pipeline, adapter = draft_setup
    entries = [
        {"speaker": "1", "text": "third", "start_time": 610.0, "end_time": 620.0, "confidence": 0.9},
        {"speaker": "1", "text": "first", "start_time": 10.0, "end_time": 310.0, "confidence": 0.6},
        {"speaker": "2", "text": "second", "start_time": 310.0, "end_time": 610.0, "confidence": 1.0},
    ]
    monkeypatch.setattr(
        adapter,
        "transcribe",
        lambda _path: _result(text="first second third", duration_sec=1, dialogue_entries=entries),
    )
    soundfile.write(input_dir / "sample.wav", np.zeros(620 * 8000), 8000)
    cuts = []

    def capture_cut(source, destination, start, end):
        cuts.append((start, end))
        shutil.copyfile(source, destination)

    monkeypatch.setattr(pipeline, "cut_audio", capture_cut)
    record = pipeline.generate_transcripts(input_dir)[0]
    assert record.segment_count == 2
    assert cuts == [(10, 610), (610, 620)]
    draft = pipeline.work_dir / "drafts" / record.sample_id / "draft.txt"
    assert draft.read_text() == "Speaker 1: first\nSpeaker 2: second\nSpeaker 1: third\n"
    outputs = sorted((pipeline.work_dir / "drafts" / record.sample_id / "segments").iterdir())
    assert [(output / "audio.txt").read_text() for output in outputs] == [
        "Speaker 1: first\nSpeaker 2: second\n",
        "Speaker 1: third\n",
    ]
    metadata = json.loads((outputs[0] / "metadata.json").read_text())
    assert "segment_count" not in metadata
    assert metadata["mean_utterance_confidence"] == pytest.approx(0.8)
    assert metadata["std_utterance_confidence"] == pytest.approx(0.2)
    assert metadata["source_start_seconds"] == 10
    last = json.loads((outputs[1] / "metadata.json").read_text())
    assert "segment_count" not in last
    assert last["source_start_seconds"] == 610
    assert last["source_end_seconds"] == 620


@pytest.mark.parametrize(("end_time", "expected_status"), [(1.0, "completed"), (1.03, "completed"), (1.5, "failed")])
def test_end_times_are_accepted_within_the_timestamp_tolerance(draft_setup, monkeypatch, end_time, expected_status):
    # The source audio is exactly one second long and the tolerance is 50 ms.
    input_dir, pipeline, adapter = draft_setup
    monkeypatch.setattr(
        adapter,
        "transcribe",
        lambda _path: _result(
            dialogue_entries=[{"speaker": "1", "text": "hi", "start_time": 0.0, "end_time": end_time}]
        ),
    )
    record = pipeline.generate_transcripts(input_dir)[0]
    assert record.status == expected_status
    if expected_status == "failed":
        assert "exceed the audio duration" in record.error


def test_mixed_batch_records_each_sample_independently(draft_setup, monkeypatch):
    input_dir, pipeline, adapter = draft_setup
    shutil.copyfile(input_dir / "sample.wav", input_dir / "broken.wav")

    def transcribe(wav_path: str) -> TranscriptionResult:
        if "/broken-" in wav_path:
            return _result("", debug_info={"error": "service failed"}, dialogue_entries=[])
        return _result()

    monkeypatch.setattr(adapter, "transcribe", transcribe)
    records = pipeline.generate_transcripts(input_dir)
    assert {record.source_audio: record.status for record in records} == {
        "broken.wav": "failed",
        "sample.wav": "completed",
    }


@pytest.mark.parametrize(
    ("entries", "expected_text", "delete_fails"),
    [
        ([{"speaker": "1", "text": "hello", "start_time": 0.0, "end_time": 1.0, "confidence": 0.9}], "hello", False),
        ([], "", False),
        ([{"speaker": "1", "text": "hello", "start_time": 0.0, "end_time": 1.0, "confidence": 0.9}], "hello", True),
    ],
)
def test_azure_batch_path_uploads_polls_and_deletes_temporary_audio(
    tmp_path, monkeypatch, caplog, entries, expected_text, delete_fails
):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake audio")
    calls = {"uploads": [], "checks": 0, "deletes": []}

    class FakeStorage:
        name = "s3"

        async def upload(self, key, path):
            calls["uploads"].append((key, path))

        async def delete(self, key):
            calls["deletes"].append(key)
            if delete_fails:
                message = "storage delete failed"
                raise OSError(message)

    async def fake_start(_adapter, recording):
        assert recording.s3_file_key == calls["uploads"][0][0]
        return SimpleNamespace(job_name="job")

    async def fake_check(_adapter, _job):
        calls["checks"] += 1
        if calls["checks"] == 1:
            return SimpleNamespace(job_status="Running", transcript=None)
        return SimpleNamespace(
            job_status="Succeeded",
            transcript=entries,
        )

    monkeypatch.setattr(pipeline_module, "get_storage_service", lambda _name: FakeStorage())
    monkeypatch.setattr(pipeline_module, "BATCH_TRANSCRIPTION_POLL_SECONDS", 0)
    monkeypatch.setattr(pipeline_module.AzureBatchTranscriptionAdapter, "start", classmethod(fake_start))
    monkeypatch.setattr(pipeline_module.AzureBatchTranscriptionAdapter, "check", classmethod(fake_check))

    pipeline = SilverTranscriptPipeline(tmp_path / "work")
    result = asyncio.run(pipeline._transcribe_with_azure_batch(audio_path, 7200))  # noqa: SLF001

    assert result.text == expected_text
    if entries:
        assert result.dialogue_entries[0]["confidence"] == pytest.approx(0.9)
    assert len(calls["uploads"]) == 1
    assert calls["checks"] == 2
    assert calls["deletes"] == [calls["uploads"][0][0]]
    if delete_fails:
        assert "Could not delete temporary batch audio" in caplog.text


def test_batch_timeout_retains_audio_for_the_running_job(tmp_path, monkeypatch, caplog):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake audio")
    calls = {"deletes": [], "checks": 0}

    class FakeStorage:
        name = "s3"

        async def upload(self, _key, _path):
            pass

        async def delete(self, key):
            calls["deletes"].append(key)

    async def fake_start(_adapter, _recording):
        return SimpleNamespace(job_name="job")

    async def fake_check(_adapter, _job):
        calls["checks"] += 1
        return SimpleNamespace(job_status="Running", transcript=None)

    monkeypatch.setattr(pipeline_module, "get_storage_service", lambda _name: FakeStorage())
    monkeypatch.setattr(pipeline_module, "MIN_BATCH_TRANSCRIPTION_TIMEOUT_SECONDS", 0)
    monkeypatch.setattr(pipeline_module.AzureBatchTranscriptionAdapter, "start", classmethod(fake_start))
    monkeypatch.setattr(pipeline_module.AzureBatchTranscriptionAdapter, "check", classmethod(fake_check))

    pipeline = SilverTranscriptPipeline(tmp_path / "work")
    with pytest.raises(TimeoutError, match="did not complete within 0 minutes"):
        asyncio.run(pipeline._transcribe_with_azure_batch(audio_path, 0))  # noqa: SLF001

    assert calls["checks"] == 0
    assert calls["deletes"] == []
    assert "Retaining silver-transcripts/" in caplog.text


def test_batch_path_rejects_local_storage_before_upload(tmp_path, monkeypatch):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake audio")

    class LocalStorage:
        name = "local"

        async def upload(self, _key, _path):
            pytest.fail("local storage must be rejected before upload")

    monkeypatch.setattr(pipeline_module, "get_storage_service", lambda _name: LocalStorage())
    pipeline = SilverTranscriptPipeline(tmp_path / "work")

    with pytest.raises(ValueError, match="STORAGE_SERVICE_NAME=local"):
        asyncio.run(pipeline._transcribe_with_azure_batch(audio_path, 7200))  # noqa: SLF001


def test_transcription_rejects_audio_over_batch_limit(tmp_path):
    pipeline = SilverTranscriptPipeline(tmp_path / "work")

    with pytest.raises(ValueError, match="supports up to 4 hours"):
        pipeline._transcribe(Path("audio.mp3"), pipeline_module.MAX_BATCH_TRANSCRIPTION_SECONDS + 1, True)  # noqa: SLF001


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
    # The service adapter retries and then raises tenacity's RetryError, which is none of the
    # exception types a transcription failure was once expected to arrive as.
    input_dir, pipeline, adapter = draft_setup
    shutil.copyfile(input_dir / "sample.wav", input_dir / "broken.wav")

    def transcribe(wav_path: str) -> TranscriptionResult:
        if "/broken-" in wav_path:
            raise _exhausted_retry(httpx.ConnectError("azure is unreachable"))
        return _result()

    monkeypatch.setattr(adapter, "transcribe", transcribe)
    records = pipeline.generate_transcripts(input_dir)

    assert {record.source_audio: record.status for record in records} == {
        "broken.wav": "failed",
        "sample.wav": "completed",
    }
    failed = _only_failure(records)
    # The cause, not tenacity's wrapper: its repr names a Future at a memory address instead.
    assert failed.error == "azure is unreachable (after 5 attempts)"
    saved = json.loads((pipeline.work_dir / "drafts" / failed.sample_id / "metadata.json").read_text())
    assert saved["error"] == failed.error


@pytest.mark.parametrize("cause", [TypeError("unexpected type"), KeyError("missing"), ZeroDivisionError("nope")])
def test_an_unlisted_service_error_is_recorded_and_the_batch_continues(draft_setup, monkeypatch, cause):
    # Containment must not depend on naming the exception types the service can raise.
    input_dir, pipeline, adapter = draft_setup
    shutil.copyfile(input_dir / "sample.wav", input_dir / "broken.wav")

    def transcribe(wav_path: str) -> TranscriptionResult:
        if "/broken-" in wav_path:
            raise cause
        return _result()

    monkeypatch.setattr(adapter, "transcribe", transcribe)
    records = pipeline.generate_transcripts(input_dir)

    assert {record.source_audio: record.status for record in records} == {
        "broken.wav": "failed",
        "sample.wav": "completed",
    }
    assert _only_failure(records).error


@pytest.mark.parametrize("status", ["pending_review", "approved"])
def test_a_status_from_an_earlier_version_fails_only_its_own_sample(draft_setup, status):
    # Statuses are edited by hand, so an unknown one must neither abandon the batch nor cost the
    # draft it was written in: its author needs the file intact to correct it.
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
    # Annotation happens on files moved out of the draft tree, so a completed metadata.json is the
    # only record that a draft is done; its segments need not still be on disk to resume.
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
    # segment_count is provenance for the run that produced it, not an invariant to re-verify.
    input_dir, pipeline, adapter = draft_setup
    original = pipeline.generate_transcripts(input_dir)
    path = pipeline.work_dir / "drafts" / original[0].sample_id / "metadata.json"
    metadata = json.loads(path.read_text()) | {"segment_count": 2}
    path.write_text(json.dumps(metadata), encoding="utf-8")

    assert pipeline.generate_transcripts(input_dir)[0].segment_count == 2
    assert adapter.calls == 1


@pytest.mark.parametrize("end", [1.5, float("inf"), float("nan")])
def test_invalid_utterance_duration_fails_generation(draft_setup, monkeypatch, end):
    input_dir, pipeline, adapter = draft_setup
    monkeypatch.setattr(
        adapter,
        "transcribe",
        lambda _path: _result(
            text="too long",
            duration_sec=1,
            dialogue_entries=[{"speaker": "1", "text": "too long", "start_time": 0, "end_time": end}],
        ),
    )
    record = pipeline.generate_transcripts(input_dir)[0]
    assert record.status == "failed"
    assert not list((pipeline.work_dir / "drafts").glob("*/segments/*/audio.mp3"))


def test_source_paths_are_relative_in_segment_metadata(draft_setup):
    input_dir, pipeline, _adapter = draft_setup
    nested = input_dir / "meetings"
    nested.mkdir()
    (input_dir / "sample.wav").rename(nested / "sample.wav")
    record = pipeline.generate_transcripts(input_dir)[0]
    assert record.source_audio == "meetings/sample.wav"
    path = pipeline.work_dir / "drafts" / record.sample_id / "segments" / "segment_0000" / "metadata.json"
    metadata = json.loads(path.read_text())
    assert metadata["source_audio"] == "meetings/sample.wav"
    assert str(input_dir) not in json.dumps(metadata)


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


@pytest.mark.parametrize(
    ("scores", "expected"),
    [([None, 0.0, 1.0], (2, 0.5, 0.5)), ([None], (0, None, None))],
)
def test_confidence_statistics_ignore_explicit_nulls(scores, expected):
    utterances = [
        {"speaker": "1", "text": "hello", "start_time": 0, "end_time": 1, "confidence": score} for score in scores
    ]
    assert MeetingMetadata.confidence_statistics(utterances) == expected


def _write_config(config_dir: Path, body: str) -> Path:
    config_dir.mkdir(exist_ok=True)
    config = config_dir / "smoke_test.yaml"
    config.write_text(body, encoding="utf-8")
    return config


def test_smoke_config_runs_generation_with_relative_paths(draft_setup, monkeypatch, tmp_path):
    _input_dir, _pipeline, adapter = draft_setup
    config = _write_config(tmp_path / "configs", "input_dir: ../input\nwork_dir: ../smoke_output\ncutoff_seconds: 30\n")
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.ServiceTranscriptionAdapter",
        lambda _service: adapter,
    )
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])
    monkeypatch.chdir(config.parent)

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 0
    metadata_paths = list((tmp_path / "smoke_output" / "drafts").glob("*/metadata.json"))
    assert len(metadata_paths) == 1
    metadata = json.loads(metadata_paths[0].read_text())
    assert metadata["status"] == "completed"
    assert metadata["cutoff_seconds"] == 30
    assert adapter.calls == 1


def test_main_uses_patched_adapter_for_long_input_without_calling_azure_batch(draft_setup, monkeypatch, tmp_path):
    _input_dir, _pipeline, adapter = draft_setup
    config = _write_config(tmp_path / "configs", "input_dir: ../input\nwork_dir: ../long_output\n")
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.ServiceTranscriptionAdapter",
        lambda _service: adapter,
    )
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.soundfile.info",
        lambda _path: SimpleNamespace(frames=7201, samplerate=1),
    )
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 0
    assert adapter.calls == 1
    records = list((tmp_path / "long_output" / "drafts").glob("*/metadata.json"))
    metadata = json.loads(records[0].read_text())
    assert metadata["engine"] == "test_engine"


def test_recorded_generation_failure_exits_non_zero(draft_setup, monkeypatch, tmp_path):
    _input_dir, _pipeline, adapter = draft_setup
    adapter.fail = True
    config = _write_config(tmp_path / "configs", "input_dir: ../input\nwork_dir: ../failed_output\n")
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.ServiceTranscriptionAdapter",
        lambda _service: adapter,
    )
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 1
    metadata_paths = list((tmp_path / "failed_output" / "drafts").glob("*/metadata.json"))
    assert json.loads(metadata_paths[0].read_text())["status"] == "failed"


def test_a_skipped_sample_exits_non_zero(draft_setup, monkeypatch, tmp_path):
    _input_dir, _pipeline, adapter = draft_setup
    config = _write_config(tmp_path / "configs", "input_dir: ../input\nwork_dir: ../legacy_output\n")
    sample_id = SilverTranscriptPipeline._sample_id("sample.wav", "sample")  # noqa: SLF001
    draft_dir = tmp_path / "legacy_output" / "drafts" / sample_id
    draft_dir.mkdir(parents=True)
    (draft_dir / "metadata.json").write_text('{"status": "approved"}', encoding="utf-8")
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.ServiceTranscriptionAdapter",
        lambda _service: adapter,
    )
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 1
    assert adapter.calls == 0
    assert json.loads((draft_dir / "metadata.json").read_text()) == {"status": "approved"}


def test_generate_reports_a_missing_config(monkeypatch, tmp_path):
    missing = tmp_path / "configs" / "absent.yaml"
    monkeypatch.setattr("sys.argv", ["main", "--config", str(missing)])

    with pytest.raises(FileNotFoundError, match="Config file not found"):
        main()


def test_generate_requires_an_input_dir_in_the_config(monkeypatch, tmp_path):
    config = tmp_path / "no_input.yaml"
    config.write_text("work_dir: ../output/smoke\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])

    with pytest.raises(ValueError, match="input_dir must be specified"):
        main()


@pytest.mark.parametrize(("cutoff", "sizes"), [(30, [1, 1]), (60, [2])])
def test_configurable_cutoff_keeps_utterances_whole(cutoff, sizes):
    entries = [
        {"speaker": "1", "text": "first", "start_time": 0, "end_time": 25},
        {"speaker": "1", "text": "second", "start_time": 25, "end_time": 50},
    ]
    groups = SilverTranscriptPipeline.group_utterances(entries, cutoff)
    assert [len(group) for group in groups] == sizes


def test_changed_cutoff_does_not_silently_reuse_drafts(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    pipeline.generate_transcripts(input_dir)
    changed = SilverTranscriptPipeline(pipeline.work_dir, adapter, cutoff_seconds=30)
    with pytest.raises(ValueError, match="different cutoff_seconds"):
        changed.generate_transcripts(input_dir)
    assert adapter.calls == 1
