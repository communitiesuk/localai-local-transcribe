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


@pytest.mark.parametrize(
    ("kwargs", "expected_size", "expected_overlap"),
    [
        ({}, 1000, 400),
        ({"chunk_size_chars": 2000, "overlap_chars": 400}, 2000, 400),
    ],
)
def test_chunking_config(kwargs: dict, expected_size: int, expected_overlap: int) -> None:
    config = ChunkingConfig(**kwargs)
    assert config.chunk_size_chars == expected_size
    assert config.overlap_chars == expected_overlap


def test_evals_config() -> None:
    config = EvalsConfig()
    assert isinstance(config.chunking, ChunkingConfig)

    custom = EvalsConfig(chunking=ChunkingConfig(chunk_size_chars=500, overlap_chars=100))
    assert custom.chunking.chunk_size_chars == 500
    assert custom.chunking.overlap_chars == 100


@pytest.mark.parametrize(
    ("chunk", "span_text", "expected"),
    [
        (
            "I remember that With my first child it was very hard.",
            "With my first child",
            "my first child",
        ),
        ("my first child was born in summer.", "my first child", "my first child"),
        ("juggling act with the kids every day.", "juggling act with the kids", "juggling act with the kids"),
    ],
)
def test_strip_leading_with(chunk: str, span_text: str, expected: str) -> None:
    start = chunk.index(span_text)
    end = start + len(span_text)
    new_start = _strip_leading_with(start, end, chunk)
    assert chunk[new_start:end] == expected


@pytest.mark.parametrize(
    ("transcript", "pos", "expected"),
    [
        ("hello world", 0, 0),
        ("hello world", 6, 6),
        ("individuals with disabilities", 3, 12),
        ("hello", 3, 3),
    ],
)
def test_align_to_word_start(transcript: str, pos: int, expected: int) -> None:
    assert _align_to_word_start(transcript, pos) == expected


def test_build_chunks_starts_on_word_boundaries() -> None:
    transcript = "aaa " * 300
    chunks = build_chunks(transcript, chunk_size_chars=1000, overlap_chars=400)
    for _text, offset in chunks:
        if offset > 0:
            assert transcript[offset - 1] == " ", f"Chunk at offset {offset} starts mid-word"


def test_build_chunks_respects_chunk_size() -> None:
    transcript = "a" * 3000
    chunks = build_chunks(transcript, chunk_size_chars=1000, overlap_chars=0)
    assert len(chunks) == 3
    assert all(len(text) == 1000 for text, _ in chunks)


@pytest.mark.parametrize(
    ("length", "chunk_size", "overlap", "expected_offsets"),
    [
        (1500, 1000, 500, [0, 500, 1000]),
        (2500, 1000, 250, [0, 750, 1500, 2250]),
    ],
)
def test_build_chunks_offsets(length: int, chunk_size: int, overlap: int, expected_offsets: list[int]) -> None:
    chunks = build_chunks("a" * length, chunk_size_chars=chunk_size, overlap_chars=overlap)
    assert [offset for _, offset in chunks] == expected_offsets


def test_build_chunks_larger_overlap_produces_more_chunks() -> None:
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
def test_build_chunks_covers_full_transcript(chunk_size: int, overlap: int) -> None:
    transcript = "abc" * 600
    chunks = build_chunks(transcript, chunk_size_chars=chunk_size, overlap_chars=overlap)
    last_text, last_offset = chunks[-1]
    assert last_offset + len(last_text) >= len(transcript)


def test_deduplication_merges_same_category_and_value() -> None:
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3)])
    b = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 10, 13)])
    result = deduplicate_characteristics([a, b])
    assert len(result) == 1
    assert len(result[0].evidence_spans) == 2


def test_deduplication_keeps_distinct_categories() -> None:
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3)])
    b = _make_detection(ProtectedCharacteristic.SEX, "Male", [("Raj", 0, 3)])
    result = deduplicate_characteristics([a, b])
    assert len(result) == 2


def test_deduplication_merges_overlapping_spans_same_category() -> None:
    """Same name, same characteristic, different attribute_value strings → merge into one entry."""
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian (name proxy)", [("Raj", 0, 3)], confidence=0.85)
    b = _make_detection(
        ProtectedCharacteristic.RACE, "South Asian (Indian name proxy)", [("Raj", 0, 3)], confidence=0.90
    )
    result = deduplicate_characteristics([a, b])
    assert len(result) == 1
    assert result[0].attribute_value == "South Asian (Indian name proxy)"
    assert result[0].confidence == 0.90


def test_deduplication_does_not_merge_non_overlapping_entries() -> None:
    """Same characteristic and different attribute_value but completely different spans → keep separate."""
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3)])
    b = _make_detection(ProtectedCharacteristic.RACE, "West African", [("Kofi", 50, 54)])
    result = deduplicate_characteristics([a, b])
    assert len(result) == 2


def test_upgrade_subspans_cross_characteristic() -> None:
    """'Blum' (137-141) in Religion upgraded to 'Mrs Blum' (133-141) from Sex entry."""
    sex_entry = _make_detection(ProtectedCharacteristic.SEX, "Female", [("Mrs Blum", 133, 141)])
    religion_entry = _make_detection(ProtectedCharacteristic.RELIGION_BELIEF, "Jewish", [("Blum", 137, 141)])
    entries = [sex_entry, religion_entry]
    _upgrade_subspans_to_longest(entries)
    religion_span = religion_entry.evidence_spans[0]
    assert religion_span.start_index == 133
    assert religion_span.end_index == 141
    assert religion_span.text == "Mrs Blum"


def test_upgrade_subspans_no_change_when_already_longest() -> None:
    entry = _make_detection(ProtectedCharacteristic.SEX, "Female", [("Mrs Ahmed", 0, 9)])
    _upgrade_subspans_to_longest([entry])
    assert entry.evidence_spans[0].start_index == 0
    assert entry.evidence_spans[0].text == "Mrs Ahmed"


def test_upgrade_does_not_promote_to_long_phrase() -> None:
    long_phrase = "Both as an amputee and as someone who is blind"
    assert len(long_phrase) > _MAX_UPGRADE_SPAN_LEN
    long_entry = _make_detection(ProtectedCharacteristic.DISABILITY, "Amputee", [(long_phrase, 0, len(long_phrase))])
    short_entry = _make_detection(ProtectedCharacteristic.DISABILITY, "Amputee", [("an amputee", 8, 18)])
    _upgrade_subspans_to_longest([long_entry, short_entry])
    assert short_entry.evidence_spans[0].text == "an amputee"


def test_deduplication_merges_subspan_same_category() -> None:
    """'Blum' (702-706) contained within 'Mrs Blum' (698-706) → merged into one Race entry."""
    a = _make_detection(ProtectedCharacteristic.RACE, "Jewish surname proxy", [("Mrs Blum", 698, 706)])
    b = _make_detection(ProtectedCharacteristic.RACE, "Jewish surname", [("Blum", 702, 706)])
    result = deduplicate_characteristics([a, b])
    assert len(result) == 1
    assert all(s.start_index == 698 for s in result[0].evidence_spans)


@pytest.mark.parametrize(
    ("spans", "expected_count", "expected_first_text"),
    [
        (
            [
                TextSpan(text="individuals with disabilities", start_index=10, end_index=39),
                TextSpan(text="with disabilities", start_index=22, end_index=39),
            ],
            1,
            "individuals with disabilities",
        ),
        (
            [
                TextSpan(text="Mrs Ahmed", start_index=0, end_index=9),
                TextSpan(text="Kofi", start_index=20, end_index=24),
            ],
            2,
            None,
        ),
    ],
)
def test_remove_subspans(spans: list[TextSpan], expected_count: int, expected_first_text: str | None) -> None:
    result = _remove_subspans(spans)
    assert len(result) == expected_count
    if expected_first_text is not None:
        assert result[0].text == expected_first_text


def test_deduplication_no_duplicate_span_positions() -> None:
    a = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3), ("Raj", 10, 13)])
    b = _make_detection(ProtectedCharacteristic.RACE, "South Asian", [("Raj", 0, 3)])
    result = deduplicate_characteristics([a, b])
    assert len(result) == 1
    assert len(result[0].evidence_spans) == 2
