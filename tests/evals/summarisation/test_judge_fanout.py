"""``call_llm_judge_parallel`` must run every dimension concurrently and leave nothing running behind.

Two properties, neither of which was covered before. The dimensions fan out with no warm-up call in
front of them: awaiting one first to prime a prompt-prefix cache serialises a round trip on every
path, and on the paths that judge one summary per transcript it doubles judge wall-clock. And when one
dimension fails, its siblings are cancelled and drained rather than left holding the semaphore with an
exception nobody retrieves.
"""

from __future__ import annotations

import asyncio

import pytest

from evals.summarisation.src.common import metric as metric_module
from evals.summarisation.src.common.metric import RubricEvaluation, call_llm_judge_parallel
from evals.summarisation.src.constants import CONCURRENCY

_TRANSCRIPT = "[0] Officer: The application was signed off.\n[1] Customer: Understood."

# One per concurrency slot, so a correct implementation can have all of them in flight at once and a
# warm-up call in front of the fan-out shows up as a lower peak.
_DIMENSIONS = ["accuracy", "readability", "auditability", "coverage"][:CONCURRENCY]


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
    """Records how many judge calls were ever in flight at the same moment.

    ``hold_others`` keeps every non-failing call suspended indefinitely, so a failure surfaces while
    its siblings are genuinely mid-flight — the state in which real judge calls are abandoned. Without
    it the siblings finish first and the orphan case is never exercised.
    """

    def __init__(self, *, fail_on_call: int | None = None, hold_others: bool = False) -> None:
        self.in_flight = 0
        self.peak = 0
        self.calls = 0
        self._fail_on_call = fail_on_call
        self._hold_others = hold_others

    async def __call__(self, _messages) -> RubricEvaluation:
        self.calls += 1
        should_fail = self.calls == self._fail_on_call
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        # Yield so every sibling task gets to enter before any of them leaves.
        await asyncio.sleep(0)
        if self._hold_others and not should_fail:
            await asyncio.Event().wait()  # cancelled by the caller's cleanup, or the test hangs
        self.in_flight -= 1
        if should_fail:
            msg = "judge rejected the request"
            raise RuntimeError(msg)
        return RubricEvaluation(dimensions=[])


def test_every_dimension_is_in_flight_at_once(monkeypatch):
    """A warm-up call awaited ahead of the fan-out caps the peak one below the dimension count."""
    tracker = _Tracker()
    _install_adapter(monkeypatch, tracker)

    asyncio.run(_judge(_DIMENSIONS))

    assert tracker.peak == len(_DIMENSIONS)


def test_a_failing_dimension_does_not_prevent_its_siblings_starting(monkeypatch):
    """With a warm-up in front, a failure on the first dimension meant the rest were never created."""
    tracker = _Tracker(fail_on_call=1)
    _install_adapter(monkeypatch, tracker)

    with pytest.raises(RuntimeError):
        asyncio.run(_judge(_DIMENSIONS))

    assert tracker.peak == len(_DIMENSIONS)


def test_a_failure_leaves_no_judge_work_running(monkeypatch):
    """Siblings abandoned by ``gather`` keep the semaphore and never have their exception retrieved.

    The failing call is the last one, so the others are still awaiting when it raises. A bare
    ``gather`` returns and strands them; the cleanup must cancel and drain them instead.
    """
    tracker = _Tracker(fail_on_call=len(_DIMENSIONS), hold_others=True)
    _install_adapter(monkeypatch, tracker)

    async def scenario() -> set[asyncio.Task]:
        with pytest.raises(RuntimeError):
            await _judge(_DIMENSIONS)
        return {task for task in asyncio.all_tasks() if task is not asyncio.current_task()}

    assert asyncio.run(scenario()) == set()


def test_no_dimensions_is_not_an_error(monkeypatch):
    """``judged_dimensions`` can filter the list down to nothing when a template cannot cite."""
    tracker = _Tracker()
    _install_adapter(monkeypatch, tracker)

    assert asyncio.run(_judge([])) == {"dimensions": {}}
    assert tracker.calls == 0
