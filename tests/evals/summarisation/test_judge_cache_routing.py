"""A shared prefix only becomes a cache hit if repeat calls reach the replica holding it.

Azure routes on ``prompt_cache_key``, so every judge call over one transcript must send the same key.
Without it, routing is chance and the shared prefix is wasted on most calls.
"""

from __future__ import annotations

import asyncio

import pytest

from evals.summarisation.src.common import metric as metric_module
from evals.summarisation.src.common.metric import RubricEvaluation, call_llm_judge, call_llm_judge_parallel
from evals.summarisation.src.judge import judge_cache_key

_TRANSCRIPT = "[0] Officer: The application was signed off.\n[1] Customer: Understood."


@pytest.fixture
def recording_adapter(monkeypatch):
    """Capture the ``prompt_cache_key`` of every judge call, returning a canned score."""
    seen: list[str | None] = []

    class _Adapter:
        async def structured_chat(self, _messages, _response_format, *, prompt_cache_key=None):
            seen.append(prompt_cache_key)
            return RubricEvaluation(dimensions=[])

    monkeypatch.setattr(metric_module, "build_azure_apim_adapter", _Adapter)
    return seen


def test_cache_key_is_stable_for_one_transcript():
    assert judge_cache_key(_TRANSCRIPT) == judge_cache_key(_TRANSCRIPT)


def test_cache_key_differs_between_transcripts():
    assert judge_cache_key(_TRANSCRIPT) != judge_cache_key(_TRANSCRIPT + "\n[2] Officer: Closed.")


def test_cache_key_is_a_plain_digest_of_the_transcript():
    """Unlike the boundary marker, this must not be random per run.

    A key that rotated per process would stop consecutive runs sharing a warm cache, and it needs no
    secrecy — it routes requests, it does not authenticate a boundary.
    """
    import hashlib

    assert judge_cache_key(_TRANSCRIPT) == hashlib.sha256(_TRANSCRIPT.encode()).hexdigest()[:32]


def test_cache_key_is_not_the_boundary_marker():
    """Sending the marker as request metadata would publish the anti-injection token needlessly."""
    from evals.summarisation.src.judge import judge_marker_hash

    assert judge_cache_key(_TRANSCRIPT) != judge_marker_hash(_TRANSCRIPT)


def test_every_dimension_call_sends_the_same_cache_key(recording_adapter):
    asyncio.run(
        call_llm_judge_parallel(
            summary_id="s1",
            transcript_ref="t1",
            transcript_text=_TRANSCRIPT,
            summary_text="Signed off [0].",
            dimensions=["accuracy", "readability", "auditability"],
        )
    )

    assert recording_adapter == [judge_cache_key(_TRANSCRIPT)] * 3


def test_call_llm_judge_forwards_the_cache_key(recording_adapter):
    asyncio.run(call_llm_judge("sys", "user", prompt_cache_key="abc123"))

    assert recording_adapter == ["abc123"]
