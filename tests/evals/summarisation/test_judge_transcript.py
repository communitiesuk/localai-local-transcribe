"""The judge must see the transcript with the same entry numbering the citation step used.

The production summariser cites claims as ``[n]`` markers indexing transcript entries. If the
judge is shown an unnumbered transcript, those markers point at nothing it can check, so the
auditability score measures the judge's inability to verify rather than the summary's
traceability. These tests pin the numbering at every judge call site.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from common.templates.citations import combine_consecutive_citations
from evals.summarisation.src.judge import build_user_message
from evals.summarisation.src.optimisation.runner import judge_transcript_from_dialogue
from evals.summarisation.src.transcript import citation_markers, judge_transcript_text

_ENTRIES = [
    {"speaker": "Housing Officer", "text": "The application was signed off.", "start_time": 0.0, "end_time": 1.0},
    {"speaker": "Customer", "text": "That's a relief.", "start_time": 1.0, "end_time": 2.0},
]


def test_judge_transcript_text_numbers_entries_from_zero():
    rendered = judge_transcript_text(_ENTRIES)

    assert rendered.splitlines() == [
        "[0] Housing Officer: The application was signed off.",
        "[1] Customer: That's a relief.",
    ]


def test_judge_transcript_from_dialogue_numbers_dialogsum_lines():
    rendered = judge_transcript_from_dialogue("#Person1#: Hello.\n#Person2#: Hi.")

    assert rendered.splitlines() == ["[0] Person1: Hello.", "[1] Person2: Hi."]


# --- standard eval ---


def test_standard_eval_judges_against_numbered_transcript(eval_config, run_standard_eval, judge_scoring_5):
    judge = judge_scoring_5(["auditability"])

    run_standard_eval(
        eval_config(template_name="General", metrics=["auditability"]),
        judge=judge,
        dialogue="#A#: We agreed the deadline.\n#B#: Understood.",
        summary="Deadline agreed [0].",
        total_claims=1,
    )

    assert judge.await_args.kwargs["transcript_text"] == "[0] A: We agreed the deadline.\n[1] B: Understood."


# --- security eval ---


def test_security_eval_judges_against_numbered_transcript(monkeypatch, tmp_path):
    import json

    from evals.summarisation.src.common import load_config
    from evals.summarisation.src.security import runner as runner_module
    from evals.summarisation.src.security.runner import run_security_eval

    scenario = {
        "scenario_id": "demo__benign",
        "base_transcript": "demo",
        "injection_level": "benign",
        "intended_solicitation": "note",
        "dialogue_entries": _ENTRIES,
    }
    input_dir = tmp_path / "scenarios"
    input_dir.mkdir()
    (input_dir / "a_benign.json").write_text(json.dumps(scenario), encoding="utf-8")

    seen: dict[str, str] = {}

    async def fake_generate_summary(_entries, _template_name=None):
        return SimpleNamespace(text="Signed off [0].", total_claims=1, hallucinations=[])

    async def fake_judge(*, dimensions, transcript_text, **_kwargs):
        seen["transcript_text"] = transcript_text
        return {"dimensions": {d: {"score": 5, "rationale": f"rationale for {d}"} for d in dimensions}}

    monkeypatch.setattr(runner_module, "generate_summary", fake_generate_summary)
    monkeypatch.setattr(runner_module, "call_llm_judge_parallel", fake_judge)

    cfg = load_config("evals/summarisation/configs/security.yaml")
    cfg.run.output_dir = str(tmp_path / "out")

    asyncio.run(run_security_eval(cfg, input_dir, Path(cfg.run.output_dir)))

    assert seen["transcript_text"] == judge_transcript_text(_ENTRIES)


# --- bias eval ---


def test_bias_iteration_judges_against_numbered_transcript():
    from evals.summarisation.src.bias import iteration_runner as iteration_module

    seen: dict[str, str] = {}

    class _RecordingMetric:
        name = "auditability"

        async def evaluate_async(self, *, example, prediction):  # noqa: ARG002
            seen["dialogue"] = example.dialogue
            # bias records judge scores normalised to [0, 1]
            return SimpleNamespace(score=1.0, reason="cited")

    class _Sentiment:
        def compute_sentiment_distribution(self, _summary):
            return {"positive": 1.0, "neutral": 0.0, "negative": 0.0}

    async def fake_generate_summary(_entries, _template_name=None):
        return SimpleNamespace(text="Signed off [0].", total_claims=1, hallucinations=[])

    with patch.object(iteration_module, "generate_summary", fake_generate_summary):
        asyncio.run(
            iteration_module.run_single_iteration(
                dialogue_entries=_ENTRIES,
                iteration_id="it-0",
                metrics=[_RecordingMetric()],
                sentiment_analyzer=_Sentiment(),
            )
        )

    assert seen["dialogue"] == judge_transcript_text(_ENTRIES)


# --- the judge is told, mechanically, which markers the summary really contains ---
#
# See ``citation_markers`` for why: left to read markers off the summary, the judge invents them.


def test_citation_markers_finds_single_and_range_markers():
    summary = "Signed off [11]. Discussed at length [4-6]. Not a marker [see annex] or [].".strip()

    assert citation_markers(summary, n_entries=20) == ["[11]", "[4-6]"]


def test_citation_markers_empty_for_uncited_summary():
    assert citation_markers("The Housing Officer confirmed the application was signed off.", n_entries=20) == []


@pytest.mark.parametrize("indices", [[1, 3], [1, 2, 4, 6], [5, 7], [80, 81], [0], [11, 12]])
def test_citation_markers_reads_back_everything_the_citation_step_writes(indices):
    """Pinned to the real producer: a marker form it emits but we don't parse is invisible evidence.

    The judge is told the extracted list is the summary's real citations, so a form the regex misses
    is reported to it as an absence — a correctly cited summary judged as uncited.
    """
    cited = combine_consecutive_citations("Claim " + "".join(f"[{i}]" for i in indices))

    markers = citation_markers(cited, n_entries=max(indices) + 1)
    covered = {int(n) for marker in markers for n in re.findall(r"\d+", marker)}

    assert covered, f"no markers recovered from {cited!r}"
    assert min(covered) == min(indices)
    assert max(covered) == max(indices)


def test_citation_markers_reads_the_comma_form_the_citing_model_emits():
    """`cite_claims.j2` warns against `[80, 81]`, which is evidence the model produces it."""
    assert citation_markers("Masha and Hero were well matched [5, 7].", n_entries=20) == ["[5, 7]"]


def test_citation_markers_ignores_bracketed_numbers_outside_the_transcript():
    """Otherwise a stray bracketed year turns an uncited summary into a 'cited' one."""
    assert citation_markers("The [2024-2025] budget rose.", n_entries=20) == []


def test_citation_markers_collapses_repeats_so_the_count_reads_as_coverage():
    assert citation_markers("Agreed [3]. Confirmed [3]. Noted [4].", n_entries=20) == ["[3]", "[4]"]


def _user_message(summary_text: str, target_dimension: str | None = None) -> str:
    return build_user_message(
        summary_id="s1",
        transcript_ref="t1",
        transcript_text=judge_transcript_text(_ENTRIES),
        summary_text=summary_text,
        target_dimension=target_dimension,
        marker_hash="abc123",
    )


def test_user_message_states_when_summary_has_no_citation_markers():
    message = _user_message("The Housing Officer confirmed the application was signed off.")

    assert "contains no citation markers" in message


def test_user_message_does_not_excuse_a_summary_for_having_no_citations():
    """Auditability is skipped outright for templates that can't cite (`judged_dimensions`).

    So the no-markers branch only ever runs for a template that was *supposed* to cite, where the
    absence is a failed citation step. Telling the judge it is "expected rather than a malfunction"
    there turns a total loss of the citation feature into a mediocre-but-plausible score.
    """
    message = _user_message("The Housing Officer confirmed the application was signed off.")

    assert "expected here rather than a malfunction" not in message


def test_user_message_lists_the_markers_a_cited_summary_contains():
    message = _user_message("Signed off [0]. Acknowledged [1].")

    assert "contains no citation markers" not in message
    assert "[0], [1]" in message


# --- rubric wording matches the mechanism the product actually uses ---


@pytest.mark.parametrize("marker", ["[n]", "numbered"])
def test_auditability_rubric_describes_index_citations(marker):
    prompt = _user_message("Signed off [0].", target_dimension="auditability")

    assert marker in prompt


def test_auditability_rubric_does_not_require_timestamps_unconditionally():
    """A transcript with no timestamps must still be able to reach the top score."""
    prompt = _user_message("Signed off [0].", target_dimension="auditability")

    assert "timestamps accurate and consistently formatted; fully auditable" not in prompt
