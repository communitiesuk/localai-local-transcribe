"""
tests/evals/test_regard_scorer.py

Unit tests for REGARDScorer.

Design goals
------------
* Zero network I/O — the HuggingFace model and tokeniser are replaced by
  lightweight stubs via pytest-mock (already in the repo's dev deps).
* Zero GPU requirement — device is forced to "cpu".
* Fast — no real forward passes; stubs return deterministic tensors.
* Mirrors the repo's existing test style: pytest functions, plain asserts,
  monkeypatch / MagicMock via pytest-mock.

Run with:
    make test
or directly:
    poetry run pytest tests/evals/test_regard_scorer.py -v
"""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch

# ---------------------------------------------------------------------------
# Stub factories
# ---------------------------------------------------------------------------

def _make_stub_tokenizer() -> MagicMock:
    """
    Minimal tokeniser stub.

    encode()  → one token-ID per whitespace word (good enough for window tests)
    decode()  → reconstructs a string with that many placeholder words
    __call__  → returns fake PT tensors with the right batch/seq shapes
    """
    tok = MagicMock()

    tok.encode.side_effect = lambda text, **kw: list(range(len(text.split())))

    tok.decode.side_effect = lambda ids, **kw: " ".join("w" for _ in ids)

    def _batch_encode(
        texts: list[str],
        padding: bool = True,
        truncation: bool = True,
        max_length: int = 512,
        return_tensors: str = "pt",
    ) -> dict[str, torch.Tensor]:
        batch = len(texts)
        seq = max((len(t.split()) for t in texts), default=1) + 2  # +2 for CLS/SEP
        seq = min(seq, max_length)
        return {
            "input_ids": torch.zeros(batch, seq, dtype=torch.long),
            "attention_mask": torch.ones(batch, seq, dtype=torch.long),
        }

    tok.side_effect = _batch_encode
    return tok


def _make_stub_model(logit_rows: list[list[float]] | None = None) -> MagicMock:
    """
    Minimal model stub.

    id2label uses the canonical ordering so _col_indices resolves correctly.

    logit_rows: optional list of [pos, neu, neg, other] logits to return
                per call, cycling if the batch is larger than the list.
                Defaults to equal logits → softmax → 0.25 each.
    """
    model = MagicMock()
    model.config.id2label = {0: "positive", 1: "neutral", 2: "negative", 3: "other"}
    model.eval.return_value = model
    model.to.return_value = model

    default_row = [0.0, 0.0, 0.0, 0.0]  # equal logits → 0.25 each after softmax

    def _forward(**kwargs: Any) -> MagicMock:
        batch_size = kwargs["input_ids"].shape[0]
        rows = logit_rows or [default_row]
        batch_logits = [rows[i % len(rows)] for i in range(batch_size)]
        out = MagicMock()
        out.logits = torch.tensor(batch_logits, dtype=torch.float32)
        return out

    model.__call__ = _forward
    # MagicMock's __call__ doesn't wire through __call__ directly; patch it:
    model.side_effect = _forward
    return model


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_TOK_PATH = "evals.summarisation.src.bias.regard_scorer.AutoTokenizer.from_pretrained"
_MOD_PATH = "evals.summarisation.src.bias.regard_scorer.AutoModelForSequenceClassification.from_pretrained"

# When running the file directly (not inside the package), fall back to the
# local module name used during development.
_TOK_PATH_LOCAL = "regard_scorer.AutoTokenizer.from_pretrained"
_MOD_PATH_LOCAL = "regard_scorer.AutoModelForSequenceClassification.from_pretrained"


def _build_scorer(
    stub_tok: MagicMock | None = None,
    stub_mod: MagicMock | None = None,
) -> Any:
    """Instantiate REGARDScorer with stubs, trying both import paths."""
    tok = stub_tok or _make_stub_tokenizer()
    mod = stub_mod or _make_stub_model()

    for tok_path, mod_path in [
        (_TOK_PATH, _MOD_PATH),
        (_TOK_PATH_LOCAL, _MOD_PATH_LOCAL),
    ]:
        try:
            with patch(tok_path, return_value=tok), patch(mod_path, return_value=mod):
                try:
                    from evals.summarisation.src.bias.regard_scorer import REGARDScorer
                except ModuleNotFoundError:
                    from regard_scorer import REGARDScorer  # type: ignore[no-redef]
                return REGARDScorer(device="cpu")
        except ModuleNotFoundError:
            continue

    raise ImportError("Could not import REGARDScorer via any known path.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_constants() -> tuple[int, int, int]:
    try:
        from evals.summarisation.src.bias.regard_scorer import (
            _OVERLAP_TOKENS,
            _STRIDE,
            _WINDOW_TOKENS,
        )
    except ModuleNotFoundError:
        from regard_scorer import _OVERLAP_TOKENS, _STRIDE, _WINDOW_TOKENS  # type: ignore[no-redef]
    return _WINDOW_TOKENS, _OVERLAP_TOKENS, _STRIDE


# ===========================================================================
# 1. Chunking tests  (no model calls)
# ===========================================================================

class TestChunking:
    """Validate the sliding-window logic in _chunk_text."""

    def test_short_text_produces_single_chunk(self) -> None:
        scorer = _build_scorer()
        chunks, counts = scorer._chunk_text("word " * 10)
        assert len(chunks) == 1
        assert counts[0] == 10

    def test_empty_text_returns_empty(self) -> None:
        scorer = _build_scorer()
        chunks, counts = scorer._chunk_text("")
        assert chunks == []
        assert counts == []

    def test_exact_window_size_is_one_chunk(self) -> None:
        window, _, _ = _import_constants()
        scorer = _build_scorer()
        chunks, counts = scorer._chunk_text("word " * window)
        assert len(chunks) == 1
        assert counts[0] == window

    def test_one_token_over_window_produces_two_chunks(self) -> None:
        window, _, _ = _import_constants()
        scorer = _build_scorer()
        chunks, counts = scorer._chunk_text("word " * (window + 1))
        assert len(chunks) == 2

    def test_long_text_produces_multiple_chunks(self) -> None:
        scorer = _build_scorer()
        # 900 words → well over one 462-token window
        chunks, counts = scorer._chunk_text("word " * 900)
        assert len(chunks) > 1

    def test_final_chunk_reflects_actual_token_count(self) -> None:
        """
        The last chunk's recorded count must equal its real length,
        not _WINDOW_TOKENS — this is the core of the token-weighting fix.
        """
        window, _, stride = _import_constants()
        scorer = _build_scorer()

        # Construct a total length where the remainder is exactly 100 tokens.
        remainder = 100
        total = window + stride + remainder  # forces 3 chunks; last has `remainder` tokens
        chunks, counts = scorer._chunk_text("word " * total)

        assert counts[-1] == len(chunks[-1])
        assert counts[-1] < window

    def test_chunk_overlap_is_correct(self) -> None:
        """Consecutive chunks should share exactly _OVERLAP_TOKENS tokens."""
        window, overlap, stride = _import_constants()
        scorer = _build_scorer()

        total = window + stride  # exactly two chunks
        chunks, _ = scorer._chunk_text("word " * total)
        assert len(chunks) == 2

        # The tail of chunk[0] should equal the head of chunk[1]
        shared = chunks[0][-overlap:]
        assert shared == chunks[1][:overlap]

    def test_all_tokens_covered(self) -> None:
        """Every source token must appear in at least one chunk."""
        window, _, stride = _import_constants()
        scorer = _build_scorer()

        # Use distinct IDs so we can verify coverage
        total = window + stride + 50
        # Override encode to return unique IDs
        scorer._tokenizer.encode.side_effect = lambda text, **kw: list(
            range(len(text.split()))
        )
        chunks, _ = scorer._chunk_text("word " * total)

        seen = set()
        for chunk in chunks:
            seen.update(chunk)

        assert seen == set(range(total))

    def test_token_counts_match_chunk_lengths(self) -> None:
        scorer = _build_scorer()
        chunks, counts = scorer._chunk_text("word " * 600)
        for chunk, count in zip(chunks, counts):
            assert len(chunk) == count


# ===========================================================================
# 2. Scoring / aggregation tests
# ===========================================================================

class TestScoring:
    """Validate score_summary() output and weighted aggregation."""

    def test_uniform_logits_produce_quarter_probabilities(self) -> None:
        scorer = _build_scorer()  # default stub → equal logits → 0.25 each
        result = scorer.score_summary("word " * 20)

        for val in result.distribution.as_dict().values():
            assert abs(val - 0.25) < 1e-5

    def test_distribution_sums_to_one(self) -> None:
        scorer = _build_scorer()
        result = scorer.score_summary("word " * 50)
        total = sum(result.distribution.as_dict().values())
        assert abs(total - 1.0) < 1e-5

    def test_chunk_count_correct_for_short_text(self) -> None:
        scorer = _build_scorer()
        result = scorer.score_summary("word " * 10)
        assert result.chunk_count == 1

    def test_total_tokens_correct_for_short_text(self) -> None:
        scorer = _build_scorer()
        result = scorer.score_summary("word " * 10)
        assert result.total_tokens == 10

    def test_empty_text_returns_uniform_fallback(self) -> None:
        scorer = _build_scorer()
        result = scorer.score_summary("")
        assert result.chunk_count == 0
        assert result.total_tokens == 0
        for val in result.distribution.as_dict().values():
            assert abs(val - 0.25) < 1e-5

    def test_negative_property_matches_distribution(self) -> None:
        scorer = _build_scorer()
        result = scorer.score_summary("word " * 30)
        assert result.negative == result.distribution.negative

    def test_token_weighted_average_skews_toward_larger_chunk(self) -> None:
        """
        When the first chunk has strongly negative logits and the second
        (smaller) chunk has strongly positive logits, the weighted average
        should skew negative because the first chunk has more tokens.
        """
        window, _, stride = _import_constants()

        # Chunk 1: 462 tokens, very negative logits
        # Chunk 2: ~50 tokens (remainder), very positive logits
        # If weighting is wrong (uniform), positive would pull more.
        # If weighting is correct (by actual count), negative should dominate.
        negative_row = [-10.0, -10.0, 10.0, -10.0]   # neg ≈ 1.0
        positive_row = [-10.0, -10.0, -10.0, -10.0]   # all equal after softmax

        call_count = 0

        def _forward(**kwargs: Any) -> MagicMock:
            nonlocal call_count
            batch = kwargs["input_ids"].shape[0]
            rows = []
            for _ in range(batch):
                rows.append(negative_row if call_count == 0 else positive_row)
                call_count += 1
            out = MagicMock()
            out.logits = torch.tensor(rows, dtype=torch.float32)
            return out

        stub_mod = _make_stub_model()
        stub_mod.side_effect = _forward

        scorer = _build_scorer(stub_mod=stub_mod)

        # Force two chunks: first = window tokens, second = 50 tokens
        total = window + 50
        scorer._tokenizer.encode.side_effect = lambda text, **kw: list(
            range(len(text.split()))
        )
        result = scorer.score_summary("word " * total)
# Check that it's NOT uniform
uniform_avg = 0.5 * (1.0 + 0.25) # (neg_chunk_val + pos_chunk_val) / 2
assert abs(result.distribution.negative - uniform_avg) > 0.05
        # Negative should dominate given the larger first chunk
        assert result.distribution.negative > 0.5

    def test_delta_negative_is_none_for_standalone_call(self) -> None:
        scorer = _build_scorer()
        result = scorer.score_summary("word " * 10)
        assert result.delta_negative is None

    def test_debug_dict_contains_expected_keys(self) -> None:
        scorer = _build_scorer()
        result = scorer.score_summary("word " * 10)
        d = result.debug_dict()
        assert set(d.keys()) == {"distribution", "chunk_count", "total_tokens", "delta_negative"}
        assert set(d["distribution"].keys()) == {"positive", "neutral", "negative", "other"}


# ===========================================================================
# 3. score_pair() tests
# ===========================================================================

class TestScorePair:
    """Validate the paired scoring interface and delta_negative computation."""

    def test_delta_negative_is_zero_for_identical_inputs(self) -> None:
        scorer = _build_scorer()
        pair = scorer.score_pair("word " * 20, "word " * 20)
        assert abs(pair.delta_negative) < 1e-6

    def test_delta_negative_sign_reflects_more_negative_counterfactual(self) -> None:
        """
        When counterfactual has higher negative probability, delta_negative > 0.
        """
        neutral_row = [0.0, 10.0, 0.0, 0.0]   # neutral ≈ 1.0 → negative ≈ 0
        negative_row = [0.0, 0.0, 10.0, 0.0]  # negative ≈ 1.0

        call_index = 0

        def _forward(**kwargs: Any) -> MagicMock:
            nonlocal call_index
            batch = kwargs["input_ids"].shape[0]
            # First score_summary call = factual (neutral), second = counterfactual (negative)
            row = neutral_row if call_index == 0 else negative_row
            call_index += batch
            out = MagicMock()
            out.logits = torch.tensor([row] * batch, dtype=torch.float32)
            return out

        stub_mod = _make_stub_model()
        stub_mod.side_effect = _forward

        scorer = _build_scorer(stub_mod=stub_mod)
        pair = scorer.score_pair("word " * 10, "word " * 10)

        assert pair.delta_negative > 0

    def test_delta_negative_attached_to_child_results(self) -> None:
        scorer = _build_scorer()
        pair = scorer.score_pair("word " * 10, "word " * 15)
        assert pair.factual.delta_negative == pair.delta_negative
        assert pair.counterfactual.delta_negative == pair.delta_negative

    def test_pair_debug_dict_structure(self) -> None:
        scorer = _build_scorer()
        pair = scorer.score_pair("word " * 10, "word " * 10)
        d = pair.debug_dict()
        assert "delta_negative" in d
        assert "factual" in d
        assert "counterfactual" in d

    def test_factual_and_counterfactual_scored_independently(self) -> None:
        """Different length inputs should produce different total_tokens."""
        scorer = _build_scorer()
        pair = scorer.score_pair("word " * 5, "word " * 50)
        assert pair.factual.total_tokens != pair.counterfactual.total_tokens

    def test_delta_negative_formula(self) -> None:
        """delta_negative == cf.negative - factual.negative, always."""
        scorer = _build_scorer()
        pair = scorer.score_pair("word " * 20, "word " * 20)
        expected = pair.counterfactual.negative - pair.factual.negative
        assert abs(pair.delta_negative - expected) < 1e-10


# ===========================================================================
# 4. REGARDDistribution helper tests
# ===========================================================================

class TestREGARDDistribution:
    def test_as_dict_returns_all_four_keys(self) -> None:
        try:
            from evals.summarisation.src.bias.regard_scorer import REGARDDistribution
        except ModuleNotFoundError:
            from regard_scorer import REGARDDistribution  # type: ignore[no-redef]

        d = REGARDDistribution(positive=0.4, neutral=0.3, negative=0.2, other=0.1)
        result = d.as_dict()
        assert result == {"positive": 0.4, "neutral": 0.3, "negative": 0.2, "other": 0.1}


# ===========================================================================
# 5. Edge cases
# ===========================================================================

class TestEdgeCases:
    def test_single_word_input(self) -> None:
        scorer = _build_scorer()
        result = scorer.score_summary("hello")
        assert result.chunk_count == 1
        assert result.total_tokens == 1

    def test_batch_size_one_produces_same_result_as_batch_size_eight(self) -> None:
        """Batching should not affect the final distribution."""
        tok = _make_stub_tokenizer()
        mod = _make_stub_model()

        for tok_path, mod_path in [
            (_TOK_PATH, _MOD_PATH),
            (_TOK_PATH_LOCAL, _MOD_PATH_LOCAL),
        ]:
            try:
                with patch(tok_path, return_value=tok), patch(mod_path, return_value=mod):
                    try:
                        from evals.summarisation.src.bias.regard_scorer import REGARDScorer
                    except ModuleNotFoundError:
                        from regard_scorer import REGARDScorer  # type: ignore[no-redef]

                    s1 = REGARDScorer(device="cpu", batch_size=1)
                    s8 = REGARDScorer(device="cpu", batch_size=8)
                    break
            except ModuleNotFoundError:
                continue

        text = "word " * 200
        r1 = s1.score_summary(text)
        r8 = s8.score_summary(text)

        for key in ("positive", "neutral", "negative", "other"):
            assert abs(r1.distribution.as_dict()[key] - r8.distribution.as_dict()[key]) < 1e-5

    def test_very_long_text_does_not_raise(self) -> None:
        scorer = _build_scorer()
        # 5 000 words — exercises many batches of chunks
        scorer.score_summary("word " * 5_000)
