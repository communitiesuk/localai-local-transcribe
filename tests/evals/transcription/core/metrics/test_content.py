import json

import pytest

from evals.transcription.src.core.metrics.content import normalise_content
from evals.transcription.src.core.results import _wer_by_group, create_summary, save_results
from evals.transcription.src.core.runner import _compute_all_metrics
from evals.transcription.src.models import EngineOutput, SampleRow, TimingAccumulator


def _evaluate_samples(samples):
    rows = []
    for sample in samples:
        reference = sample.get("reference_dialogue_entries")
        hypothesis = sample.get("hypothesis_dialogue_entries")
        metrics = _compute_all_metrics(
            sample["reference_transcript"], sample["hypothesis_transcript"], reference, hypothesis, 0.5
        )
        rows.append(
            SampleRow(
                run_id="test",
                timestamp="test",
                engine_version="test",
                latency_ms=1,
                reference_dialogue_entries=None,
                hypothesis_dialogue_entries=None,
                **{
                    key: value
                    for key, value in sample.items()
                    if key not in {"reference_dialogue_entries", "hypothesis_dialogue_entries"}
                },
                metrics=metrics.model_dump(exclude_none=True),
            )
        )
    summary = create_summary("test", rows, TimingAccumulator(), "test", "test", "test", None)
    return rows, summary


def test_normalise_content_removes_fillers_but_keeps_meaningful_backchannels():
    assert normalise_content("Um, YEAH... mm-hmm okay!") == "yeah okay"


def test_standard_content_wer_and_weighted_corpus():
    samples = [
        {"example_id": "0", "reference_transcript": "Um the quick fox", "hypothesis_transcript": "the quick fox"},
        {"example_id": "1", "reference_transcript": "hello world", "hypothesis_transcript": "hello there"},
    ]
    rows, summary = _evaluate_samples(samples)
    assert rows[0].metrics["content_wer"] == 0
    assert rows[1].metrics["content_wer"] == pytest.approx(0.5)
    assert summary.corpus_content_wer == pytest.approx(0.2)
    assert summary.metrics["content_wer"].mean == pytest.approx(0.25)


def test_standard_content_wer_by_dialect():
    samples = [
        {
            "example_id": "0",
            "reference_transcript": "hello world",
            "hypothesis_transcript": "hello there",
            "sample_metadata": {"group": "welsh_female", "dialect": "welsh", "gender": "female"},
        }
    ]
    rows, _summary = _evaluate_samples(samples)
    group = _wer_by_group(rows)["welsh_female"]
    assert group["corpus_content_wer"] == pytest.approx(0.5)
    assert group["content_wer"]["mean"] == pytest.approx(0.5)


def test_standard_evaluation_outputs_content_wer_and_weighted_summary():
    rows = []
    for index, (reference, hypothesis) in enumerate([("um one two three", "one two three"), ("uh four five", "four")]):
        metrics = _compute_all_metrics(reference, hypothesis, None, None, 0.5)
        assert metrics.wer > metrics.content_wer
        rows.append(
            SampleRow(
                run_id="test",
                timestamp="test",
                example_id=str(index),
                engine_version="test",
                reference_transcript=reference,
                hypothesis_transcript=hypothesis,
                reference_dialogue_entries=None,
                hypothesis_dialogue_entries=None,
                latency_ms=1,
                metrics=metrics.model_dump(exclude_none=True),
            )
        )
    summary = create_summary("test", rows, TimingAccumulator(), "test", "test", "test", None)
    assert summary.metrics["content_wer"].mean == pytest.approx(0.25)
    assert summary.corpus_content_wer == pytest.approx(0.2)


@pytest.mark.parametrize(("reference", "hypothesis", "expected_insertions"), [("um", "uh", 0), ("um", "hello", 1)])
def test_standard_evaluation_content_wer_with_only_fillers(reference, hypothesis, expected_insertions):
    """A filler-only reference has no scorable rate, but its edit counts stay exact."""

    metrics = _compute_all_metrics(reference, hypothesis, None, None, 0.5)
    assert metrics.content_wer is None
    assert metrics.content_reference_words == 0
    assert metrics.content_insertions == expected_insertions


def test_saved_results_include_content_wer_with_standard_diarization_metrics(tmp_path):
    rows, summary = _evaluate_samples(
        [
            {
                "example_id": "0",
                "reference_transcript": "um hello there",
                "hypothesis_transcript": "hello there",
                "reference_dialogue_entries": [{"speaker": "a", "text": "um hello there", "start": 0, "end": 1}],
                "hypothesis_dialogue_entries": [{"speaker": "b", "text": "hello there", "start": 0, "end": 1}],
            }
        ]
    )
    output = tmp_path / "results.json"
    save_results([EngineOutput(summary=summary, samples=rows)], output)
    saved = json.loads(output.read_text())
    metrics = saved["engines"]["test"][0]["metrics"]
    assert metrics["content_wer"] == 0
    assert metrics["wer"] == pytest.approx(1 / 3)
    assert metrics["wder"] == 0
    assert metrics["speaker_count_accuracy"] == 1
    assert set(saved["summaries"][0]["metrics"]) == {
        "wer",
        "content_wer",
        "wder",
        "speaker_count_accuracy",
        "processing_speed_ratio",
    }
    assert saved["summaries"][0]["corpus_content_wer"] == 0
    assert not any("chunk_local" in key or "content_wder" in key for key in metrics)
    assert not any("chunk_local" in key or "content_wder" in key for key in saved["summaries"][0])


@pytest.mark.parametrize("hypothesis", ["uh", "hello world"])
def test_empty_content_reference_reports_no_rate_at_sample_and_corpus_level(hypothesis):
    """With no content reference words anywhere, every content rate is unavailable."""
    rows, summary = _evaluate_samples(
        [
            {
                "example_id": "0",
                "reference_transcript": "erm um",
                "hypothesis_transcript": hypothesis,
                "sample_metadata": {"group": "welsh_female", "dialect": "welsh", "gender": "female"},
            }
        ]
    )
    group = _wer_by_group(rows)["welsh_female"]
    assert "content_wer" not in rows[0].metrics
    assert summary.corpus_content_wer is None
    assert group["corpus_content_wer"] is None
    assert group["content_wer"] is None


def test_empty_content_reference_still_contributes_insertions_to_corpus():
    """The unscorable sample's insertions must survive into the corpus numerator."""
    rows, summary = _evaluate_samples(
        [
            # No content reference words, two spurious hypothesis words.
            {
                "example_id": "0",
                "reference_transcript": "erm um",
                "hypothesis_transcript": "hello world",
                "sample_metadata": {"group": "welsh_female", "dialect": "welsh", "gender": "female"},
            },
            # Two content reference words, matched exactly.
            {
                "example_id": "1",
                "reference_transcript": "hello there",
                "hypothesis_transcript": "hello there",
                "sample_metadata": {"group": "welsh_female", "dialect": "welsh", "gender": "female"},
            },
        ]
    )
    group = _wer_by_group(rows)["welsh_female"]

    assert "content_wer" not in rows[0].metrics
    assert rows[1].metrics["content_wer"] == 0

    # 2 insertions over 2 reference words, rather than the 0.0 a dropped sample would give.
    assert summary.corpus_content_wer == pytest.approx(1.0)
    assert group["corpus_content_wer"] == pytest.approx(1.0)
    assert group["content_errors"] == 2
    assert group["content_reference_words"] == 2

    # The mean averages only the one scorable sample; the unscorable one does not skew it.
    assert summary.metrics["content_wer"].mean == pytest.approx(0.0)
    assert group["content_wer"]["mean"] == pytest.approx(0.0)


def test_summary_without_content_scores_reports_unavailable():
    rows, _ = _evaluate_samples(
        [{"example_id": "0", "reference_transcript": "hello", "hypothesis_transcript": "hello"}]
    )
    rows[0].metrics = {key: value for key, value in rows[0].metrics.items() if not key.startswith("content_")}
    summary = create_summary("test", rows, TimingAccumulator(), "test", "test", "test", None)
    assert summary.corpus_content_wer is None
    assert "content_wer" not in summary.metrics
