from __future__ import annotations

import json
import shutil
from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest
import soundfile
from ffmpeg import Error as FFmpegError

from common.audio.ffmpeg import convert_to_mp3
from common.services.transcription_services.azure_stt_base import convert_to_dialogue_entries
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

@pytest.fixture
def draft_setup(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    soundfile.write(input_dir / "sample.wav", np.zeros(16000), 16000)
    monkeypatch.setattr("evals.dataset_generation.silver_transcripts.src.pipeline.convert_to_mp3", shutil.copyfile)
    adapter = DraftAdapter()
    pipeline = SilverTranscriptPipeline(tmp_path / "work", adapter)
    monkeypatch.setattr(pipeline, "cut_audio", _copy_cut)
    return input_dir, pipeline, adapter


def test_generation_writes_segment_files(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    records = pipeline.generate_transcripts(input_dir)
    sample_id = records[0].sample_id
    folder = pipeline.work_dir / "drafts" / sample_id / "segments" / "segment_0000"
    assert records[0].status == "completed"
    assert records[0].engine == "test_engine"
    meeting_dir = pipeline.work_dir / "drafts" / sample_id
    assert not (meeting_dir / "transcript.txt").exists()
    assert (meeting_dir / "draft.txt").read_text() == "the original draft\n"
    (folder / "transcript.txt").write_text("the corrected reference", encoding="utf-8")
    assert (folder / "transcript.txt").read_text() == "the corrected reference"
    provenance = json.loads((folder / "metadata.json").read_text())
    assert provenance["status"] == "completed"
    assert not {"standard", "source_sha256", "audio_sha256", "draft_sha256", "dialogue_entries"} & provenance.keys()
    assert not (folder / "draft.txt").exists()
    assert adapter.calls == 1


def test_rerunning_generation_preserves_review_edits(draft_setup):
    input_dir, pipeline, adapter = draft_setup
    first = pipeline.generate_transcripts(input_dir)
    transcript = pipeline.work_dir / "drafts" / first[0].sample_id / "segments" / "segment_0000" / "transcript.txt"
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
    monkeypatch.setattr(pipeline, "cut_audio", SilverTranscriptPipeline.cut_audio)
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
    (segments / "segment_0000" / "transcript.txt").write_text("stale text", encoding="utf-8")
    (segments / "segment_0009").mkdir()

    record = pipeline.generate_transcripts(input_dir)[0]

    assert record.status == "completed"
    assert record.segment_count == 1
    # The stale folder from the longer previous run is gone, not merged into the new set.
    assert sorted(path.name for path in segments.iterdir()) == ["segment_0000"]
    assert (segments / "segment_0000" / "transcript.txt").read_text() == "the original draft\n"
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
        {"speaker": "1", "text": "first", "start_time": 10.0, "end_time": 310.0, "confidence": 0.6},
        {"speaker": "2", "text": "second", "start_time": 310.0, "end_time": 610.0, "confidence": 1.0},
        {"speaker": "1", "text": "third", "start_time": 610.0, "end_time": 620.0, "confidence": 0.9},
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
    outputs = sorted((pipeline.work_dir / "drafts" / record.sample_id / "segments").iterdir())
    assert [(output / "transcript.txt").read_text() for output in outputs] == ["first second\n", "third\n"]
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
        (folder / "transcript.txt").unlink()
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
