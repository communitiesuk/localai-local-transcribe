"""``call_llm_judge_parallel`` must warm the prompt-prefix cache, then fan out, and strand nothing.

One dimension is awaited before the rest are dispatched. Every dimension's prompt is byte-identical up
to the end of the summary, so a completed call leaves a prefix the rest hit; dispatched together they
all begin prefill with nothing to hit. Measured against APIM over 12 alternating A/B reps of 4
dimensions: 36.6% of input tokens came back cached with the warm-up against 12.9% without, on a 47.7%
ceiling. The tests here pin the dispatch order that produced the higher number, since nothing else can
detect its loss.

The second property is that a failing dimension leaves no sibling running with an exception nobody
retrieves, and that the failure reaches the caller as itself — the security runner records
``str(exc)`` against the scenario, so a wrapper would bury the message.
"""

from __future__ import annotations

import asyncio

import pytest

from evals.summarisation.src.common import metric as metric_module
from evals.summarisation.src.common.metric import RubricEvaluation, call_llm_judge_parallel
from evals.summarisation.src.constants import CONCURRENCY

_TRANSCRIPT = "[0] Officer: The application was signed off.\n[1] Customer: Understood."

# Fixed, not sliced to ``CONCURRENCY``: deriving the fixture size from the semaphore under test makes
# the concurrency assertion vacuous the moment ``CONCURRENCY`` drops to 1.
_DIMENSIONS = ["accuracy", "readability", "auditability", "coverage"]


def _install_adapter(monkeypatch, on_call):
    class _Adapter:
        async def structured_chat(self, messages, _response_format):
            return await on_call(messages)

    monkeypatch.setattr(metric_module, "build_azure_apim_adapter", _Adapter)


async def _judge(dimensions: list[str]) -> dict:
    return await call_llm_judge_parallel(
        summary_id="s1",
        transcript_ref="t1",
        transcript_text=_TRANSCRIPT,
        summary_text="Signed off [0].",
        dimensions=dimensions,
    )


class _Tracker:
    """Records concurrency and, per call, how many calls had already finished when it started."""

    def __init__(self, *, fail_on_call: int | None = None) -> None:
        self.in_flight = 0
        self.peak = 0
        self.calls = 0
        self.completed = 0
        self.completed_before_start: list[int] = []
        self._fail_on_call = fail_on_call

    async def __call__(self, _messages) -> RubricEvaluation:
        self.calls += 1
        should_fail = self.calls == self._fail_on_call
        self.completed_before_start.append(self.completed)
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        # Yield so every sibling task gets to enter before any of them leaves.
        await asyncio.sleep(0)
        self.in_flight -= 1
        self.completed += 1
        if should_fail:
            msg = "judge rejected the request"
            raise RuntimeError(msg)
        return RubricEvaluation(dimensions=[])


def test_one_dimension_completes_before_the_rest_are_dispatched(monkeypatch):
    """The warm-up. Fanned out together, every call would start with nothing completed in front."""
    tracker = _Tracker()
    _install_adapter(monkeypatch, tracker)

    asyncio.run(_judge(_DIMENSIONS))

    assert tracker.completed_before_start == [0, 1, 1, 1]


def test_the_dimensions_after_the_warm_up_still_run_concurrently(monkeypatch):
    """The warm-up must cost one round trip, not serialise the whole fan-out."""
    tracker = _Tracker()
    _install_adapter(monkeypatch, tracker)

    asyncio.run(_judge(_DIMENSIONS))

    assert tracker.peak == min(len(_DIMENSIONS) - 1, CONCURRENCY)
    assert tracker.peak > 1, "fixture too small or CONCURRENCY too low to tell concurrent from serial"


def test_a_failing_dimension_leaves_no_judge_work_running(monkeypatch):
    """Siblings must be awaited to completion, not abandoned holding the semaphore."""
    tracker = _Tracker(fail_on_call=len(_DIMENSIONS))
    _install_adapter(monkeypatch, tracker)

    async def scenario() -> set[asyncio.Task]:
        with pytest.raises(RuntimeError):
            await _judge(_DIMENSIONS)
        return {task for task in asyncio.all_tasks() if task is not asyncio.current_task()}

    assert asyncio.run(scenario()) == set()
    assert tracker.calls == len(_DIMENSIONS)


def test_a_failing_dimension_reaches_the_caller_as_itself(monkeypatch):
    """The security runner records ``str(exc)``, so an ExceptionGroup wrapper would bury the cause."""
    _install_adapter(monkeypatch, _Tracker(fail_on_call=len(_DIMENSIONS)))

    with pytest.raises(RuntimeError, match="judge rejected the request"):
        asyncio.run(_judge(_DIMENSIONS))


def test_a_failing_warm_up_does_not_fan_out(monkeypatch):
    """If the very first call is rejected, spending the remaining calls to fail the same way is waste."""
    tracker = _Tracker(fail_on_call=1)
    _install_adapter(monkeypatch, tracker)

    with pytest.raises(RuntimeError):
        asyncio.run(_judge(_DIMENSIONS))

    assert tracker.calls == 1


def test_no_dimensions_is_not_an_error(monkeypatch):
    """``judged_dimensions`` can filter the list down to nothing when a template cannot cite."""
    tracker = _Tracker()
    _install_adapter(monkeypatch, tracker)

    assert asyncio.run(_judge([])) == {"dimensions": {}}
    assert tracker.calls == 0
