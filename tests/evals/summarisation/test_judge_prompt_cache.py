"""Each dimension is judged in its own LLM call, so all but the criterion is repeated text.

The provider only serves a prompt from cache when its leading tokens are byte-identical to an
earlier one, so anything that varies between two judge calls has to sit after everything they
share. These tests pin that ordering: break it and the judge silently pays full price for the
transcript and summary on every dimension.
"""

from __future__ import annotations

import os

import dspy

from evals.summarisation.src.common.metric import DialogSummaryMetric
from evals.summarisation.src.common.schemas import DialogExample
from evals.summarisation.src.transcript import judge_transcript_text

_ENTRIES = [
    {"speaker": "Housing Officer", "text": "The application was signed off.", "start_time": 0.0, "end_time": 1.0},
    # No apostrophes or quotes: the prompt environment autoescapes, so escaped text would not
    # compare equal to the transcript as rendered here.
    {"speaker": "Customer", "text": "That is a relief.", "start_time": 1.0, "end_time": 2.0},
]
_SUMMARY = "The Housing Officer confirmed the application was signed off [0]."


def _judge_prompt(criterion: str) -> str:
    metric = DialogSummaryMetric(name=f"rubric_{criterion}", criterion=criterion, pass_threshold=4)
    system, user = metric._build_judge_messages(  # noqa: SLF001
        criterion,
        DialogExample(example_id="ex-1", dialogue=judge_transcript_text(_ENTRIES), reference_summary=None),
        dspy.Prediction(summary=_SUMMARY),
    )
    return system + user


def test_judge_prompts_share_the_transcript_and_summary_across_dimensions():
    shared = os.path.commonprefix([_judge_prompt("accuracy"), _judge_prompt("auditability")])

    assert judge_transcript_text(_ENTRIES) in shared
    assert _SUMMARY in shared


def test_the_criterion_is_the_only_thing_after_the_shared_prefix():
    accuracy = _judge_prompt("accuracy")
    auditability = _judge_prompt("auditability")
    shared = os.path.commonprefix([accuracy, auditability])

    assert "Factual Accuracy" in accuracy.removeprefix(shared)
    assert "Citation Quality" in auditability.removeprefix(shared)
