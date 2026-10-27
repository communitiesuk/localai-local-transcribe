from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile
from ffmpeg import Error as FFmpegError

from common.audio.ffmpeg import convert_to_mp3
from evals.dataset_generation.silver_transcripts.src.pipeline import (
    MAX_SAMPLE_NAME_LENGTH,
    SilverTranscriptPipeline,
)
from tests.evals.dataset_generation.silver_transcripts.support import result_factory


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
    monkeypatch.setattr(SilverTranscriptPipeline, "cut_audio", staticmethod(SilverTranscriptPipeline.cut_audio))
    sample_id = pipeline.generate_transcripts(input_dir)[0].sample_id
    audio, sample_rate = soundfile.read(pipeline.work_dir / "drafts" / sample_id / "audio.mp3")
    assert sample_rate == 16000
    assert len(audio) == 16000
    assert audio.ndim == 1
    assert adapter.calls == 1


def test_failed_conversion_is_recorded_without_calling_the_service(draft_setup, monkeypatch):
    input_dir, pipeline, adapter = draft_setup

    def fail_conversion(_source: Path, _target: Path) -> None:
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


@pytest.mark.parametrize("confidences", [[0.6, 1.0, None], [0.7], [None]])
def test_utterance_segments_do_not_store_confidence_metrics(draft_setup, monkeypatch, confidences):
    input_dir, pipeline, adapter = draft_setup
    soundfile.write(input_dir / "sample.wav", np.zeros(16000 * len(confidences)), 16000)
    utterances = []
    for index, confidence in enumerate(confidences):
        utterance = {
            "speaker": "1",
            "text": "hello",
            "start_time": float(index),
            "end_time": float(index + 1),
        }
        if confidence is not None:
            utterance["confidence"] = confidence
        utterances.append(utterance)
    monkeypatch.setattr(
        adapter,
        "transcribe",
        lambda _path: result_factory(
            text=" ".join(entry["text"] for entry in utterances), duration_sec=1, dialogue_entries=utterances
        ),
    )
    record = pipeline.generate_transcripts(input_dir)[0]
    assert record.status == "completed"
    metadata = json.loads((pipeline.work_dir / "drafts" / record.sample_id / "metadata.json").read_text())
    for field in ("utterance_count", "scored_utterance_count", "mean_utterance_confidence", "std_utterance_confidence"):
        assert field not in metadata
    draft_dir = pipeline.work_dir / "drafts" / record.sample_id
    assert not (draft_dir / "utterances.json").exists()
    assert not list((draft_dir / "segments").glob("*/utterances.json"))


def test_grouping_keeps_the_whole_recording_in_one_segment():
    entries = [
        {"speaker": "1", "text": "first", "start_time": 0, "end_time": 300},
        {"speaker": "2", "text": "second", "start_time": 300, "end_time": 900},
    ]
    groups = SilverTranscriptPipeline.group_utterances(entries)
    assert [len(group) for group in groups] == [2]


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
        lambda _path: result_factory(text="text without timestamps", duration_sec=1, dialogue_entries=[]),
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
        lambda _path: result_factory(text="first second third", duration_sec=1, dialogue_entries=entries),
    )
    soundfile.write(input_dir / "sample.wav", np.zeros(620 * 8000), 8000)
    cuts = []

    def capture_cut(source: Path, destination: Path, start: float, end: float) -> None:
        cuts.append((start, end))
        shutil.copyfile(source, destination)

    monkeypatch.setattr(pipeline, "cut_audio", capture_cut)
    record = pipeline.generate_transcripts(input_dir)[0]
    assert record.segment_count == 1
    assert cuts == [(10, 620)]
    draft = pipeline.work_dir / "drafts" / record.sample_id / "draft.txt"
    assert draft.read_text() == "Speaker 1: first\nSpeaker 2: second\nSpeaker 1: third\n"
    outputs = sorted((pipeline.work_dir / "drafts" / record.sample_id / "segments").iterdir())
    assert [(output / "audio.txt").read_text() for output in outputs] == [
        "Speaker 1: first\nSpeaker 2: second\nSpeaker 1: third\n",
    ]
    metadata = json.loads((outputs[0] / "metadata.json").read_text())
    assert "segment_count" not in metadata
    for field in ("utterance_count", "scored_utterance_count", "mean_utterance_confidence", "std_utterance_confidence"):
        assert field not in metadata
    assert metadata["source_start_seconds"] == 10
    assert metadata["source_end_seconds"] == 620


@pytest.mark.parametrize(("end_time", "expected_status"), [(1.0, "completed"), (1.03, "completed"), (1.5, "failed")])
def test_end_times_are_accepted_within_the_timestamp_tolerance(draft_setup, monkeypatch, end_time, expected_status):
    input_dir, pipeline, adapter = draft_setup
    monkeypatch.setattr(
        adapter,
        "transcribe",
        lambda _path: result_factory(
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

    def transcribe(wav_path: str):
        if "/broken-" in wav_path:
            return result_factory("", debug_info={"error": "service failed"}, dialogue_entries=[])
        return result_factory()

    monkeypatch.setattr(adapter, "transcribe", transcribe)
    records = pipeline.generate_transcripts(input_dir)
    assert {record.source_audio: record.status for record in records} == {
        "broken.wav": "failed",
        "sample.wav": "completed",
    }


@pytest.mark.parametrize("end", [1.5, float("inf"), float("nan")])
def test_invalid_utterance_duration_fails_generation(draft_setup, monkeypatch, end):
    input_dir, pipeline, adapter = draft_setup
    monkeypatch.setattr(
        adapter,
        "transcribe",
        lambda _path: result_factory(
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


def test_changed_segment_duration_does_not_silently_reuse_drafts(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    pipeline.generate_transcripts(input_dir)
    changed = SilverTranscriptPipeline(pipeline.work_dir, adapter, segment_duration_seconds=30)
    with pytest.raises(ValueError, match="different segment_duration_seconds"):
        changed.generate_transcripts(input_dir)
    assert adapter.calls == 1
