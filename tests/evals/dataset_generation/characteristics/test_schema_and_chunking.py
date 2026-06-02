from __future__ import annotations

import pytest

from evals.dataset_generation.characteristics.src.chunker import (
    _MAX_UPGRADE_SPAN_LEN,
    _align_to_word_start,
    _remove_subspans,
    _strip_leading_with,
    _upgrade_subspans_to_longest,
    build_chunks,
    deduplicate_characteristics,
)
from evals.dataset_generation.characteristics.src.schema import (
    CharacteristicDetection,
    ChunkingConfig,
    EvalsConfig,
    TextSpan,
)
from evals.dataset_generation.shared_constants import ProtectedCharacteristic


def _make_detection(
    characteristic: ProtectedCharacteristic,
    attribute_value: str,
    spans: list[tuple[str, int, int]],
    confidence: float = 0.9,
) -> CharacteristicDetection:
    return CharacteristicDetection(
        characteristic=characteristic,
        attribute_value=attribute_value,
        evidence_spans=[TextSpan(text=t, start_index=s, end_index=e) for t, s, e in spans],
        confidence=confidence,
    )


# --- ChunkingConfig ---


def test_chunking_config_defaults():
    config = ChunkingConfig()
    assert config.chunk_size_chars == 1000
    assert config.overlap_chars == 400


def test_chunking_config_custom_values():
    config = ChunkingConfig(chunk_size_chars=2000, overlap_chars=400)
    assert config.chunk_size_chars == 2000
    assert config.overlap_chars == 400


def test_evals_config_includes_chunking():
    config = EvalsConfig()
    assert hasattr(config, "chunking")
    assert isinstance(config.chunking, ChunkingConfig)


def test_evals_config_chunking_overridable():
    config = EvalsConfig(chunking=ChunkingConfig(chunk_size_chars=500, overlap_chars=100))
    assert config.chunking.chunk_size_chars == 500
    assert config.chunking.overlap_chars == 100


# --- _strip_leading_with ---


def test_strip_leading_with_removes_with_possessive():
    chunk = "I remember that With my first child it was very hard."
    start = chunk.index("With my first")
    end = start + len("With my first child")
    new_start = _strip_leading_with(start, end, chunk)
    assert chunk[new_start:end] == "my first child"


def test_strip_leading_with_no_change_when_no_leading_with():
    chunk = "my first child was born in summer."
    start = 0
    end = len("my first child")
    assert _strip_leading_with(start, end, chunk) == 0


def test_strip_leading_with_no_change_for_other_leading_words():
    chunk = "juggling act with the kids every day."
    start = 0
    end = len("juggling act with the kids")
    # 'juggling' is not 'With', should not be stripped
    assert _strip_leading_with(start, end, chunk) == 0


# --- _align_to_word_start ---


def test_align_to_word_start_already_on_boundary():
    assert _align_to_word_start("hello world", 0) == 0
    assert _align_to_word_start("hello world", 6) == 6  # 'w' after space


def test_align_to_word_start_mid_word_advances():
    # "individuals" → mid-word at position 3 should advance to next space+1
    transcript = "individuals with disabilities"
    assert _align_to_word_start(transcript, 3) == 12  # start of "with"


def test_align_to_word_start_no_space_within_bound():
    # No space found within _MAX_WORD_ALIGN_CHARS → return original position unchanged
    transcript = "hello"
    result = _align_to_word_start(transcript, 3)
    assert result == 3  # mid-word but no nearby space → keep original


def test_build_chunks_starts_on_word_boundaries():
    # Craft a transcript where a naive char-count split would land mid-word.
    # "aaa " (4 chars) x 300 = 1200 chars.  stride=600 -> chunk2 starts at 600 = 'a' (mid-word).
    transcript = "aaa " * 300
    chunks = build_chunks(transcript, chunk_size_chars=1000, overlap_chars=400)
    for _text, offset in chunks:
        if offset > 0:
            # The char just before the chunk start must be a space (word boundary)
            assert transcript[offset - 1] == " ", f"Chunk at offset {offset} starts mid-word"


# --- build_chunks ---


def test_build_chunks_respects_chunk_size():
    transcript = "a" * 3000
    chunks = build_chunks(transcript, chunk_size_chars=1000, overlap_chars=0)
    assert len(chunks) == 3
    assert all(len(text) == 1000 for text, _ in chunks)


def test_build_chunks_respects_overlap():
    transcript = "a" * 1500
    # stride = 1000 - 500 = 500, so chunks start at 0, 500, 1000
    chunks = build_chunks(transcript, chunk_size_chars=1000, overlap_chars=500)
    offsets = [offset for _, offset in chunks]
    assert offsets == [0, 500, 1000]


def test_build_chunks_offset_tracks_position():
    transcript = "x" * 2500
    chunks = build_chunks(transcript, chunk_size_chars=1000, overlap_chars=250)
    # stride = 750, so offsets: 0, 750, 1500
    offsets = [offset for _, offset in chunks]
    assert offsets[0] == 0
    assert offsets[1] == 750
    assert offsets[2] == 1500


def test_build_chunks_larger_overlap_produces_more_chunks():
    transcript = "x" * 3000
    chunks_small_overlap = build_chunks(transcript, chunk_size_chars=1000, overlap_chars=250)
    chunks_large_overlap = build_chunks(transcript, chunk_size_chars=1000, overlap_chars=500)
    assert len(chunks_large_overlap) > len(chunks_small_overlap)


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [
        (1000, 250),
        (1000, 400),
        (2000, 500),
    ],
)
def test_build_chunks_covers_full_transcript(chunk_size: int, overlap: int):
    transcript = "abc" * 600
    chunks = build_chunks(transcript, chunk_size_chars=chunk_size, overlap_chars=overlap)
    last_text, last_offset = chunks[-1]
    assert last_offset + len(last_text) >= len(transcript)


# --- deduplicate_characteristics ---


def test_deduplication_merges_same_category_and_value():
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3)])
    b = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 10, 13)])
    result = deduplicate_characteristics([a, b])
    assert len(result) == 1
    assert len(result[0].evidence_spans) == 2


def test_deduplication_keeps_distinct_categories():
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3)])
    b = _make_detection(ProtectedCharacteristic.SEX, "Male", [("Raj", 0, 3)])
    result = deduplicate_characteristics([a, b])
    assert len(result) == 2


def test_deduplication_merges_overlapping_spans_same_category():
    """Same name, same characteristic, different attribute_value strings → merge into one entry."""
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian (name proxy)", [("Raj", 0, 3)], confidence=0.85)
    b = _make_detection(
        ProtectedCharacteristic.RACE, "South Asian (Indian name proxy)", [("Raj", 0, 3)], confidence=0.90
    )
    result = deduplicate_characteristics([a, b])
    assert len(result) == 1
    # Higher-confidence attribute_value wins
    assert result[0].attribute_value == "South Asian (Indian name proxy)"
    assert result[0].confidence == 0.90


def test_deduplication_does_not_merge_non_overlapping_entries():
    """Same characteristic and different attribute_value but completely different spans → keep separate."""
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3)])
    b = _make_detection(ProtectedCharacteristic.RACE, "West African", [("Kofi", 50, 54)])
    result = deduplicate_characteristics([a, b])
    assert len(result) == 2


def test_upgrade_subspans_cross_characteristic():
    """'Blum' (137-141) in Religion upgraded to 'Mrs Blum' (133-141) from Sex entry."""
    sex_entry = _make_detection(ProtectedCharacteristic.SEX, "Female", [("Mrs Blum", 133, 141)])
    religion_entry = _make_detection(ProtectedCharacteristic.RELIGION_BELIEF, "Jewish", [("Blum", 137, 141)])
    entries = [sex_entry, religion_entry]
    _upgrade_subspans_to_longest(entries)
    religion_span = religion_entry.evidence_spans[0]
    assert religion_span.start_index == 133
    assert religion_span.end_index == 141
    assert religion_span.text == "Mrs Blum"


def test_upgrade_subspans_no_change_when_already_longest():
    """Spans that are already the longest form are not changed."""
    entry = _make_detection(ProtectedCharacteristic.SEX, "Female", [("Mrs Ahmed", 0, 9)])
    _upgrade_subspans_to_longest([entry])
    assert entry.evidence_spans[0].start_index == 0
    assert entry.evidence_spans[0].text == "Mrs Ahmed"


def test_upgrade_does_not_promote_to_long_phrase():
    """Long phrases (> _MAX_UPGRADE_SPAN_LEN) are not used as upgrade targets."""
    long_phrase = "Both as an amputee and as someone who is blind"
    assert len(long_phrase) > _MAX_UPGRADE_SPAN_LEN
    long_entry = _make_detection(ProtectedCharacteristic.DISABILITY, "Amputee", [(long_phrase, 0, len(long_phrase))])
    short_entry = _make_detection(ProtectedCharacteristic.DISABILITY, "Amputee", [("an amputee", 8, 18)])
    _upgrade_subspans_to_longest([long_entry, short_entry])
    # "an amputee" should NOT be upgraded to the long phrase
    assert short_entry.evidence_spans[0].text == "an amputee"


def test_deduplication_merges_subspan_same_category():
    """'Blum' (702-706) contained within 'Mrs Blum' (698-706) → merged into one Race entry."""
    a = _make_detection(ProtectedCharacteristic.RACE, "Jewish surname proxy", [("Mrs Blum", 698, 706)])
    b = _make_detection(ProtectedCharacteristic.RACE, "Jewish surname", [("Blum", 702, 706)])
    result = deduplicate_characteristics([a, b])
    assert len(result) == 1
    # The sub-span 'Blum' should be removed after merge because it's contained in 'Mrs Blum'
    assert all(s.start_index == 698 for s in result[0].evidence_spans)


def test_remove_subspans_removes_contained_span():
    spans = [
        TextSpan(text="individuals with disabilities", start_index=10, end_index=39),
        TextSpan(text="with disabilities", start_index=22, end_index=39),
    ]
    result = _remove_subspans(spans)
    assert len(result) == 1
    assert result[0].text == "individuals with disabilities"


def test_remove_subspans_keeps_non_contained():
    spans = [
        TextSpan(text="Mrs Ahmed", start_index=0, end_index=9),
        TextSpan(text="Kofi", start_index=20, end_index=24),
    ]
    result = _remove_subspans(spans)
    assert len(result) == 2


def test_deduplication_no_duplicate_span_positions():
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3), ("Raj", 10, 13)])
    b = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3)])  # duplicate of first span
    result = deduplicate_characteristics([a, b])
    assert len(result) == 1
    assert len(result[0].evidence_spans) == 2
