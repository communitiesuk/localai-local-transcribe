from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from evals.dataset_generation.characteristics.src.chunker import (
    _find_new_positions,
    process_chunk_parallel,
)
from evals.dataset_generation.characteristics.src.config_loader import render_prompt_for_characteristic
from evals.dataset_generation.characteristics.src.schema import (
    CharacteristicDetection,
    CharacteristicExtractionOutput,
    TextSpan,
)
from evals.dataset_generation.shared_constants import ProtectedCharacteristic


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


@pytest.fixture
def chunk_env(tmp_path: Path) -> Path:
    base = tmp_path / "agent_base.jinja2"
    base.write_text("Detect {% block characteristic_name %}{% endblock %} only.\n{{ transcript }}")
    _write_contexts(tmp_path / "characteristics")
    return base


@pytest.mark.parametrize(
    ("needle", "chunk", "expected_count", "expected_match"),
    [
        ("my little one", "Today, My little one has been keeping me busy.", 1, "My little one"),
        ("Luiz", "LUIZ is an engineer.", 1, None),
        ("Rabbi Goldstein", "Mrs Ahmed discussed her case.", 0, None),
    ],
)
def test_find_new_positions(needle: str, chunk: str, expected_count: int, expected_match: str | None) -> None:
    used: set[tuple[int, int]] = set()
    positions = _find_new_positions(needle, chunk, used)
    assert len(positions) == expected_count
    if expected_match is not None:
        assert chunk[positions[0][0] : positions[0][1]] == expected_match


def test_find_new_positions_per_item_isolation() -> None:
    chunk = "Luiz is an engineer. Later Luiz presented his work."
    race_used: set[tuple[int, int]] = set()
    sex_used: set[tuple[int, int]] = set()
    race_positions = _find_new_positions("Luiz", chunk, race_used)
    sex_positions = _find_new_positions("Luiz", chunk, sex_used)
    assert len(race_positions) == 2
    assert len(sex_positions) == 2
    assert set(race_positions) == set(sex_positions)


@pytest.mark.asyncio
async def test_process_chunk_parallel_calls_all_characteristics(chunk_env: Path) -> None:
    call_count = 0

    async def counting_structured_chat(_messages: list, _response_format: type) -> CharacteristicExtractionOutput:
        nonlocal call_count
        call_count += 1
        return CharacteristicExtractionOutput(detected_characteristics=[])

    chatbot = MagicMock()
    chatbot.structured_chat = counting_structured_chat

    await process_chunk_parallel("Luiz is an engineer.", 0, chunk_env, chatbot)

    assert call_count == len(ProtectedCharacteristic)


@pytest.mark.asyncio
async def test_process_chunk_parallel_merges_results(chunk_env: Path) -> None:
    async def mock_structured_chat(messages: list, _response_format: type) -> CharacteristicExtractionOutput:
        content = messages[0]["content"]
        if "Race" in content:
            return CharacteristicExtractionOutput(
                detected_characteristics=[_detection(ProtectedCharacteristic.RACE, "Brazilian", [_span("Luiz", 0)])]
            )
        if "Sex" in content:
            return CharacteristicExtractionOutput(
                detected_characteristics=[_detection(ProtectedCharacteristic.SEX, "Male", [_span("Luiz", 0)])]
            )
        return CharacteristicExtractionOutput(detected_characteristics=[])

    chatbot = MagicMock()
    chatbot.structured_chat = mock_structured_chat

    result = await process_chunk_parallel("Luiz is a Brazilian engineer.", 0, chunk_env, chatbot)

    characteristics_found = {d.characteristic for d in result}
    assert ProtectedCharacteristic.RACE in characteristics_found
    assert ProtectedCharacteristic.SEX in characteristics_found


@pytest.mark.asyncio
async def test_process_chunk_parallel_continues_when_one_agent_fails(chunk_env: Path) -> None:
    call_count = 0

    async def partial_failing_chat(messages: list, _response_format: type) -> CharacteristicExtractionOutput:
        nonlocal call_count
        call_count += 1
        if "Sex" in messages[0]["content"]:
            msg = "Simulated failure"
            raise RuntimeError(msg)
        return CharacteristicExtractionOutput(detected_characteristics=[])

    chatbot = MagicMock()
    chatbot.structured_chat = partial_failing_chat

    result = await process_chunk_parallel("Sarah discussed her case.", 0, chunk_env, chatbot)
    assert call_count == len(ProtectedCharacteristic)
    assert all(d.characteristic != ProtectedCharacteristic.SEX for d in result)


def test_render_prompt_for_characteristic(tmp_path: Path) -> None:
    base_template = tmp_path / "agent_base.jinja2"
    base_template.write_text(
        "You are detecting only {% block characteristic_name %}{% endblock %}.\n"
        "Rules: {% block characteristic_rules %}{% endblock %}\n"
        "{{ transcript }}"
    )
    _write_contexts(tmp_path / "characteristics")
    transcript = "Ahmed, aged 67."

    prompt = render_prompt_for_characteristic(base_template, ProtectedCharacteristic.AGE, transcript)

    assert "Age" in prompt
    assert transcript in prompt
    assert "Disability" not in prompt
    assert "Race" not in prompt
