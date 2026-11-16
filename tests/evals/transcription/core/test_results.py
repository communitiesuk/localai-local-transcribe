from __future__ import annotations

import json

import pytest

from evals.transcription.src.core.results import _wer_by_group, create_summary, save_results, save_summary_results
from evals.transcription.src.models import (
    EngineOutput,
    SampleRow,
    Summary,
    TimingAccumulator,
)


def make_sample_row(
    example_id="0",
    engine_version="TestEngine",
    wer=0.1,
    hits=9,
    substitutions=1,
    deletions=0,
    insertions=0,
    wder: float | None = 0.0,
    speaker_errors=0,
    total_words=10,
    speaker_count_accuracy: float | None = 1.0,
    ref_speaker_count=2,
    hyp_speaker_count=2,
    latency_ms=1000.0,
    processing_speed_ratio=0.5,
):
    metrics = {
        "wer": wer,
        "hits": hits,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions,
        "processing_speed_ratio": processing_speed_ratio,
    }
    if wder is not None:
        metrics["wder"] = wder
        metrics["speaker_errors"] = speaker_errors
        metrics["total_words"] = total_words
    if speaker_count_accuracy is not None:
        metrics["speaker_count_accuracy"] = speaker_count_accuracy
        metrics["reference_speaker_count"] = ref_speaker_count
        metrics["predicted_speaker_count"] = hyp_speaker_count

    return SampleRow(
        run_id="test_run",
        timestamp="20260223_100000",
        example_id=example_id,
        engine_version=engine_version,
        reference_transcript="hello world",
        reference_dialogue_entries=None,
        hypothesis_transcript="hello world",
        hypothesis_dialogue_entries=None,
        metrics=metrics,
        latency_ms=latency_ms,
        error=None,
    )


def test_create_summary_basic():
    rows = [make_sample_row()]
    timing = TimingAccumulator()
    timing.process_sec = 1.0
    timing.audio_sec = 2.0

    summary = create_summary(
        "TestEngine",
        rows,
        timing,
        "test_run",
        "20260223_100000",
        "AMI_v0",
        "n2_f0.1",
    )

    expected = {
        "run_id": "test_run",
        "timestamp": "20260223_100000",
        "dataset_version": "AMI_v0",
        "engine_version": "TestEngine",
        "split": "n2_f0.1",
        "n_examples": 1,
        "processing_speed_ratio": pytest.approx(0.5),
    }
    for key, value in expected.items():
        assert getattr(summary, key) == value
    assert "wer" in summary.metrics
    assert summary.metrics["wer"].mean == pytest.approx(0.1)


def test_create_summary_multiple_samples():
    rows = [
        make_sample_row(example_id="0", wer=0.1, hits=9, substitutions=1),
        make_sample_row(
            example_id="1",
            wer=0.2,
            hits=8,
            substitutions=2,
            wder=0.1,
            speaker_errors=1,
            speaker_count_accuracy=0.0,
            hyp_speaker_count=1,
            latency_ms=1200.0,
            processing_speed_ratio=0.6,
        ),
    ]
    timing = TimingAccumulator()
    timing.process_sec = 2.0
    timing.audio_sec = 4.0

    summary = create_summary(
        "TestEngine",
        rows,
        timing,
        "test_run",
        "20260223_100000",
        "AMI_v0",
        "n2_f0.1",
    )

    expected = {
        "run_id": "test_run",
        "engine_version": "TestEngine",
        "n_examples": 2,
    }
    for key, value in expected.items():
        assert getattr(summary, key) == value
    assert "wer" in summary.metrics


def test_create_summary_no_speaker_count_accuracy():
    rows = [
        make_sample_row(
            wder=None,
            speaker_count_accuracy=None,
        ),
    ]
    timing = TimingAccumulator()
    timing.process_sec = 1.0
    timing.audio_sec = 2.0

    summary = create_summary(
        "TestEngine",
        rows,
        timing,
        "test_run",
        "20260223_100000",
        "AMI_v0",
        "n2_f0.1",
    )

    expected_fields = {
        "run_id": "test_run",
        "timestamp": "20260223_100000",
        "dataset_version": "AMI_v0",
        "engine_version": "TestEngine",
        "n_examples": 1,
        "split": "n2_f0.1",
    }
    for key, value in expected_fields.items():
        assert getattr(summary, key) == value


def test_save_results_creates_file(tmp_path):
    output_path = tmp_path / "output" / "output.json"

    sample = make_sample_row(wder=None, speaker_count_accuracy=None)

    summary = Summary(
        run_id="test_run",
        timestamp="20260223_100000",
        dataset_version="AMI_v0",
        engine_version="TestEngine",
        split="n2_f0.1",
        n_examples=1,
        metrics={},
        processing_speed_ratio=0.5,
    )

    results = [EngineOutput(summary=summary, samples=[sample])]

    save_results(results, output_path)

    assert output_path.exists()

    with output_path.open() as f:
        data = json.load(f)

    expected = {
        "summaries_count": 1,
        "engines_count": 1,
        "first_summary_engine": "TestEngine",
        "has_TestEngine": True,
        "TestEngine_samples_count": 1,
    }
    actual = {
        "summaries_count": len(data["summaries"]),
        "engines_count": len(data["engines"]),
        "first_summary_engine": data["summaries"][0]["engine_version"],
        "has_TestEngine": "TestEngine" in data["engines"],
        "TestEngine_samples_count": len(data["engines"]["TestEngine"]),
    }
    assert actual == expected

    assert data["engines"]["TestEngine"][0]["hypothesis_transcript"] == sample.hypothesis_transcript
    assert data["engines"]["TestEngine"][0]["reference_transcript"] == sample.reference_transcript


def test_save_results_groups_wer_by_group(tmp_path):
    output_path = tmp_path / "output.json"
    sample = make_sample_row(wder=None, speaker_count_accuracy=None)
    sample.sample_metadata = {"group": "irish_male", "dialect": "irish", "gender": "male", "speaker_id": "1"}
    summary = Summary(
        run_id="test_run",
        timestamp="20260223_100000",
        dataset_version="EnglishDialects_v1",
        engine_version="TestEngine",
        split="published_train_all",
        n_examples=1,
        metrics={},
        processing_speed_ratio=0.5,
    )

    save_results(
        [EngineOutput(summary=summary, samples=[sample])],
        output_path,
    )

    import json

    data = json.loads(output_path.read_text(encoding="utf-8"))
    group = data["wer_by_group"]["TestEngine"]["irish_male"]
    assert group["n_examples"] == 1
    assert group["wer"]["mean"] == pytest.approx(0.1)
    assert group["corpus_wer"] == pytest.approx(0.1)


def test_save_results_multiple_engines(tmp_path):
    output_path = tmp_path / "output.json"

    sample1 = make_sample_row(engine_version="Engine1", wder=None, speaker_count_accuracy=None)
    sample2 = make_sample_row(
        engine_version="Engine2",
        wer=0.2,
        hits=8,
        substitutions=2,
        latency_ms=1500.0,
        processing_speed_ratio=0.6,
        wder=0.0,
        speaker_count_accuracy=None,
    )

    summary1 = Summary(
        run_id="test_run",
        timestamp="20260223_100000",
        dataset_version="AMI_v0",
        engine_version="Engine1",
        split="n2_f0.1",
        n_examples=1,
        metrics={},
        processing_speed_ratio=0.5,
    )

    summary2 = Summary(
        run_id="test_run",
        timestamp="20260223_100000",
        dataset_version="AMI_v0",
        engine_version="Engine2",
        split="n2_f0.1",
        n_examples=1,
        metrics={},
        processing_speed_ratio=0.6,
    )

    results = [
        EngineOutput(summary=summary1, samples=[sample1]),
        EngineOutput(summary=summary2, samples=[sample2]),
    ]

    save_results(results, output_path)

    with output_path.open() as f:
        data = json.load(f)

    expected = {
        "summaries_count": 2,
        "engines_count": 2,
        "has_Engine1": True,
        "has_Engine2": True,
    }
    actual = {
        "summaries_count": len(data["summaries"]),
        "engines_count": len(data["engines"]),
        "has_Engine1": "Engine1" in data["engines"],
        "has_Engine2": "Engine2" in data["engines"],
    }
    assert actual == expected


def test_save_summary_results_excludes_per_sample_data(tmp_path):
    output_path = tmp_path / "summary.json"
    sample = make_sample_row(wder=None, speaker_count_accuracy=None)
    summary = Summary(
        run_id="test_run",
        timestamp="20260223_100000",
        dataset_version="AMI_v0",
        engine_version="Engine1",
        split="n1",
        n_examples=1,
        overall_score=None,
        metrics={},
        processing_speed_ratio=0.5,
    )

    save_summary_results([EngineOutput(summary=summary, samples=[sample])], output_path)

    with output_path.open() as f:
        data = json.load(f)

    assert data == {"summaries": [summary.model_dump()]}


def test_wer_grouping_uses_dataset_supplied_group_without_dialect_fields():
    sample = make_sample_row()
    sample.sample_metadata = {"group": "room_a"}
    groups = _wer_by_group([sample])
    assert set(groups) == {"room_a"}
    assert groups["room_a"]["n_examples"] == 1
    assert groups["room_a"]["corpus_wer"] == pytest.approx(0.1)


def test_ungrouped_results_omit_group_section(tmp_path):
    sample = make_sample_row()
    sample.sample_metadata = {"dataset_index": 0}
    summary = create_summary("TestEngine", [sample], TimingAccumulator(), "run", "ts", "AMI_v0", None)
    path = tmp_path / "results.json"
    save_results([EngineOutput(summary=summary, samples=[sample])], path)
    data = json.loads(path.read_text())
    assert "wer_by_group" not in data
    assert "wer_by_dialect_and_gender" not in data
