from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from evals.dataset_generation.characteristics.src.chunker import (
    _find_new_positions,
    process_chunk_parallel,
    process_chunk_per_characteristic,
)
from evals.dataset_generation.characteristics.src.config_loader import render_prompt_for_characteristic
from evals.dataset_generation.characteristics.src.schema import (
    CharacteristicDetection,
    CharacteristicExtractionOutput,
    TextSpan,
)
from evals.dataset_generation.shared_constants import ProtectedCharacteristic


def _make_chatbot_returning(detections: list[CharacteristicDetection]) -> MagicMock:
    chatbot = MagicMock()
    chatbot.structured_chat = AsyncMock(
        return_value=CharacteristicExtractionOutput(detected_characteristics=detections)
    )
    return chatbot


def _span(text: str, start: int) -> TextSpan:
    return TextSpan(text=text, start_index=start, end_index=start + len(text))


def _detection(
    char: ProtectedCharacteristic,
    value: str,
    spans: list[TextSpan],
    confidence: float = 0.9,
) -> CharacteristicDetection:
    return CharacteristicDetection(
        characteristic=char,
        attribute_value=value,
        evidence_spans=spans,
        confidence=confidence,
    )


def _write_contexts(contexts_dir: Path) -> None:
    contexts_dir.mkdir(parents=True, exist_ok=True)
    for char in ProtectedCharacteristic:
        fname = char.value.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_") + ".jinja2"
        (contexts_dir / fname).write_text(
            '{% extends "agent_base.jinja2" %}\n'
            f"{{% block characteristic_name %}}{char.value}{{% endblock %}}\n"
            f"{{% block characteristic_rules %}}Look for {char.value} evidence.{{% endblock %}}\n"
            "{% block characteristic_examples %}{% endblock %}\n"
        )


def test_find_new_positions_case_insensitive_initial_cap():
    """Model returns lowercase 'my little one'; chunk has 'My little one' (initial cap)."""
    chunk = "Today, My little one has been keeping me busy."
    used: set[tuple[int, int]] = set()
    positions = _find_new_positions("my little one", chunk, used)
    assert len(positions) == 1
    found_text = chunk[positions[0][0] : positions[0][1]]
    assert found_text == "My little one"


def test_find_new_positions_case_insensitive_all_caps():
    """Model returns 'Luiz'; chunk has 'LUIZ' (all caps — unusual but should still match)."""
    chunk = "LUIZ is an engineer."
    used: set[tuple[int, int]] = set()
    positions = _find_new_positions("Luiz", chunk, used)
    assert len(positions) == 1


def test_find_new_positions_missing_span_returns_empty():
    chunk = "Mrs Ahmed discussed her case."
    used: set[tuple[int, int]] = set()
    positions = _find_new_positions("Rabbi Goldstein", chunk, used)
    assert positions == []


def test_find_new_positions_per_item_isolation():
    chunk = "Luiz is an engineer. Later Luiz presented his work."
    race_used: set[tuple[int, int]] = set()
    sex_used: set[tuple[int, int]] = set()
    race_positions = _find_new_positions("Luiz", chunk, race_used)
    sex_positions = _find_new_positions("Luiz", chunk, sex_used)
    assert len(race_positions) == 2
    assert len(sex_positions) == 2
    assert set(race_positions) == set(sex_positions)


@pytest.mark.asyncio
async def test_process_chunk_per_characteristic_drops_unlocatable_span(tmp_path: Path):
    """Spans the model returns that cannot be found in the chunk are dropped, not kept as None."""
    chunk_text = "Mrs Ahmed discussed her housing case."
    offset = 0

    # Model returns a span for text that does NOT appear in the chunk
    phantom = _detection(
        ProtectedCharacteristic.SEX,
        "Female",
        [TextSpan(text="Mrs Khan", start_index=None, end_index=None)],
    )
    chatbot = _make_chatbot_returning([phantom])

    prompt_file = tmp_path / "sex.jinja2"
    prompt_file.write_text("Detect Sex only.\n{{ transcript }}")

    result = await process_chunk_per_characteristic(
        chunk_text, offset, ProtectedCharacteristic.SEX, prompt_file, chatbot
    )

    all_spans = [s for d in result for s in d.evidence_spans]
    assert all(s.start_index is not None for s in all_spans), "No None-indexed spans should survive"


@pytest.mark.asyncio
async def test_process_chunk_per_characteristic_locates_span_case_insensitively(tmp_path: Path):
    chunk_text = "My little one has been keeping me up at night."
    offset = 100  # non-zero to test offset is applied

    detection = _detection(
        ProtectedCharacteristic.PREGNANCY_MATERNITY,
        "Parent",
        [TextSpan(text="my little one", start_index=None, end_index=None)],
    )
    chatbot = _make_chatbot_returning([detection])

    prompt_file = tmp_path / "pm.jinja2"
    prompt_file.write_text("Detect P&M.\n{{ transcript }}")

    result = await process_chunk_per_characteristic(
        chunk_text, offset, ProtectedCharacteristic.PREGNANCY_MATERNITY, prompt_file, chatbot
    )

    assert len(result) == 1
    span = result[0].evidence_spans[0]
    assert span.start_index == 100
    assert span.text == "My little one"  # actual transcript text used, not model's version


@pytest.mark.asyncio
async def test_process_chunk_per_characteristic_allows_same_position_for_different_characteristics(
    tmp_path: Path,
):
    chunk_text = "Luiz is a brilliant engineer."
    offset = 0

    race_detection = _detection(
        ProtectedCharacteristic.RACE,
        "Brazilian",
        [TextSpan(text="Luiz", start_index=None, end_index=None)],
    )
    sex_detection = _detection(
        ProtectedCharacteristic.SEX,
        "Male",
        [TextSpan(text="Luiz", start_index=None, end_index=None)],
    )

    race_prompt = tmp_path / "race.jinja2"
    race_prompt.write_text("Detect Race.\n{{ transcript }}")
    sex_prompt = tmp_path / "sex.jinja2"
    sex_prompt.write_text("Detect Sex.\n{{ transcript }}")

    race_result = await process_chunk_per_characteristic(
        chunk_text, offset, ProtectedCharacteristic.RACE, race_prompt, _make_chatbot_returning([race_detection])
    )
    sex_result = await process_chunk_per_characteristic(
        chunk_text, offset, ProtectedCharacteristic.SEX, sex_prompt, _make_chatbot_returning([sex_detection])
    )

    assert len(race_result) == 1
    assert race_result[0].evidence_spans[0].start_index == 0
    assert len(sex_result) == 1
    assert sex_result[0].evidence_spans[0].start_index == 0


@pytest.mark.asyncio
async def test_process_chunk_parallel_calls_all_nine_characteristics(tmp_path: Path):
    chunk_text = "Luiz is an engineer."
    offset = 0

    base_template = tmp_path / "agent_base.jinja2"
    base_template.write_text(
        "Detect {% block characteristic_name %}{% endblock %} only.\n{{ transcript }}"
    )
    _write_contexts(tmp_path / "characteristics")

    call_count = 0

    async def counting_structured_chat(
        _messages: list, _response_format: type
    ) -> CharacteristicExtractionOutput:
        nonlocal call_count
        call_count += 1
        return CharacteristicExtractionOutput(detected_characteristics=[])

    chatbot = MagicMock()
    chatbot.structured_chat = counting_structured_chat

    await process_chunk_parallel(chunk_text, offset, base_template, tmp_path / "characteristics", chatbot)

    assert call_count == len(ProtectedCharacteristic), (
        f"Expected {len(ProtectedCharacteristic)} agent calls, got {call_count}"
    )


@pytest.mark.asyncio
async def test_process_chunk_parallel_merges_results(tmp_path: Path):
    chunk_text = "Luiz is a Brazilian engineer."
    offset = 0

    base_template = tmp_path / "agent_base.jinja2"
    base_template.write_text(
        "Detect {% block characteristic_name %}{% endblock %} only.\n{{ transcript }}"
    )
    _write_contexts(tmp_path / "characteristics")

    async def mock_structured_chat(
        messages: list, _response_format: type
    ) -> CharacteristicExtractionOutput:
        content = messages[0]["content"]
        if "Race" in content:
            return CharacteristicExtractionOutput(
                detected_characteristics=[
                    _detection(ProtectedCharacteristic.RACE, "Brazilian", [_span("Luiz", 0)])
                ]
            )
        if "Sex" in content:
            return CharacteristicExtractionOutput(
                detected_characteristics=[
                    _detection(ProtectedCharacteristic.SEX, "Male", [_span("Luiz", 0)])
                ]
            )
        return CharacteristicExtractionOutput(detected_characteristics=[])

    chatbot = MagicMock()
    chatbot.structured_chat = mock_structured_chat

    result = await process_chunk_parallel(
        chunk_text, offset, base_template, tmp_path / "characteristics", chatbot
    )

    characteristics_found = {d.characteristic for d in result}
    assert ProtectedCharacteristic.RACE in characteristics_found
    assert ProtectedCharacteristic.SEX in characteristics_found


@pytest.mark.asyncio
async def test_process_chunk_parallel_continues_when_one_agent_fails(tmp_path: Path):
    chunk_text = "Sarah discussed her case."
    offset = 0

    base_template = tmp_path / "agent_base.jinja2"
    base_template.write_text("Detect {% block characteristic_name %}{% endblock %}.\n{{ transcript }}")
    _write_contexts(tmp_path / "characteristics")

    call_count = 0

    async def partial_failing_chat(
        messages: list, _response_format: type
    ) -> CharacteristicExtractionOutput:
        nonlocal call_count
        call_count += 1
        content = messages[0]["content"]
        if "Sex" in content:
            msg = "Simulated failure"
            raise RuntimeError(msg)
        return CharacteristicExtractionOutput(detected_characteristics=[])

    chatbot = MagicMock()
    chatbot.structured_chat = partial_failing_chat

    result = await process_chunk_parallel(chunk_text, offset, base_template, tmp_path / "characteristics", chatbot)
    assert call_count == len(ProtectedCharacteristic)
    assert all(d.characteristic != ProtectedCharacteristic.SEX for d in result)


def test_render_prompt_for_characteristic_injects_characteristic(tmp_path: Path):
    base_template = tmp_path / "agent_base.jinja2"
    base_template.write_text(
        "You are detecting only {% block characteristic_name %}{% endblock %}.\n"
        "Rules: {% block characteristic_rules %}{% endblock %}\n"
        "{{ transcript }}"
    )
    contexts_dir = tmp_path / "characteristics"
    _write_contexts(contexts_dir)

    prompt = render_prompt_for_characteristic(
        base_template, contexts_dir, ProtectedCharacteristic.AGE, "Ahmed, aged 67."
    )

    assert "Age" in prompt
    assert "Ahmed, aged 67." in prompt
    assert "Disability" not in prompt
    assert "Race" not in prompt


def test_render_prompt_for_characteristic_includes_transcript(tmp_path: Path):
    base_template = tmp_path / "agent_base.jinja2"
    base_template.write_text("{% block characteristic_name %}{% endblock %}\n{{ transcript }}")

    contexts_dir = tmp_path / "characteristics"
    _write_contexts(contexts_dir)

    transcript = "Sarah discussed her case."
    prompt = render_prompt_for_characteristic(
        base_template, contexts_dir, ProtectedCharacteristic.SEX, transcript
    )
    assert transcript in prompt
