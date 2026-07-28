"""The judge must see the transcript with the same entry numbering the citation step used.

The production summariser cites claims as ``[n]`` markers indexing transcript entries. If the
judge is shown an unnumbered transcript, those markers point at nothing it can check, so the
auditability score measures the judge's inability to verify rather than the summary's
traceability. These tests pin the numbering at every judge call site.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from evals.summarisation.src.common import AppConfig
from evals.summarisation.src.common.transcript import citation_markers, judge_transcript_text
from evals.summarisation.src.judge import build_user_message
from evals.summarisation.src.optimisation.runner import judge_transcript_from_dialogue, run_eval

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


def _cfg(tmp_path: Path) -> AppConfig:
    return AppConfig.model_validate(
        {
            "run": {"output_dir": str(tmp_path / "output")},
            "dataset": {"name": "d", "dialogue_field": "dialogue", "reference_summary_field": "summary"},
            "judge": {"pass_threshold": 4},
            "prompts": {"judge_template_path": "prompts/judge.jinja2"},
            "metrics": ["auditability"],
        }
    )


def test_standard_eval_judges_against_numbered_transcript(tmp_path):
    dialogue = "#A#: We agreed the deadline.\n#B#: Understood."
    mock_rows = [{"id": "1", "dialogue": dialogue, "summary": "Deadline agreed"}]
    mock_split = Mock()
    mock_split.select = Mock(return_value=mock_rows)
    mock_split.__len__ = Mock(return_value=1)

    generated = Mock(text="Deadline agreed [0].", hallucinations=[], total_claims=1)
    judge = AsyncMock(return_value={"dimensions": {"auditability": {"score": "5", "rationale": "Cited"}}})

    with (
        patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value={"test": mock_split}),
        patch(
            "evals.summarisation.src.optimisation.runner.generate_summary",
            new_callable=AsyncMock,
            return_value=generated,
        ),
        patch("evals.summarisation.src.optimisation.runner.call_llm_judge_parallel", judge),
        patch("evals.summarisation.src.optimisation.runner.get_settings") as mock_settings,
        patch("evals.summarisation.src.optimisation.runner.tiktoken.encoding_for_model") as mock_tokenizer,
    ):
        mock_settings.return_value.FAST_LLM_MODEL_NAME = "test-model"
        mock_tokenizer.return_value.encode = Mock(return_value=[1])

        run_eval(_cfg(tmp_path), split="test", limit=1, prompt_version="v1")

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
# Templates with citations_required = False (Short 'n' Sweet) and the basic-minutes path emit no
# markers at all. Asked to judge such a summary against a numbered transcript, the judge invents
# markers wholesale and scores them: an observed run of Short 'n' Sweet scored 4.2/5 on rationales
# citing "[4]-[10]" against summaries containing no marker whatsoever. A mechanical extraction
# passed alongside the summary removes the judge's licence to imagine evidence.


def test_citation_markers_finds_single_and_range_markers():
    summary = "Signed off [11]. Discussed at length [4-6]. Not a marker [see annex] or [].".strip()

    assert citation_markers(summary) == ["[11]", "[4-6]"]


def test_citation_markers_empty_for_uncited_summary():
    assert citation_markers("The Housing Officer confirmed the application was signed off.") == []


def _user_message(summary_text: str) -> str:
    return build_user_message(
        summary_id="s1",
        transcript_ref="t1",
        transcript_text=judge_transcript_text(_ENTRIES),
        summary_text=summary_text,
        marker_hash="abc123",
    )


def test_user_message_states_when_summary_has_no_citation_markers():
    message = _user_message("The Housing Officer confirmed the application was signed off.")

    assert "contains no citation markers" in message


def test_user_message_lists_the_markers_a_cited_summary_contains():
    message = _user_message("Signed off [0]. Acknowledged [1].")

    assert "contains no citation markers" not in message
    assert "[0], [1]" in message


# --- rubric wording matches the mechanism the product actually uses ---


@pytest.mark.parametrize("marker", ["[n]", "numbered"])
def test_auditability_rubric_describes_index_citations(marker):
    from evals.summarisation.src.judge import build_system_prompt

    prompt = build_system_prompt("auditability", marker_hash="abc123")

    assert marker in prompt


def test_auditability_rubric_does_not_require_timestamps_unconditionally():
    """A transcript with no timestamps must still be able to reach the top score."""
    from evals.summarisation.src.judge import build_system_prompt

    prompt = build_system_prompt("auditability", marker_hash="abc123")

    assert "timestamps accurate and consistently formatted; fully auditable" not in prompt
