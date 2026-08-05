from unittest.mock import AsyncMock

import pytest

from common.database.postgres_models import DialogueEntry
from evals.dataset_generation.counterfactual_generation.src.models import (
    AxisChange,
    CharacteristicDetection,
    EvidenceSpan,
    TranscriptInput,
)
from evals.dataset_generation.counterfactual_generation.src.rewriter import CounterfactualRewriter
from evals.dataset_generation.shared_constants import ProtectedCharacteristic


@pytest.fixture
def mock_chatbot():
    return AsyncMock()


@pytest.fixture
def sample_transcript():
    entries = [
        DialogueEntry(speaker="A", text="He is a doctor", start_time=0.0, end_time=1.0),
        DialogueEntry(speaker="B", text="Yes, he works at the hospital", start_time=1.0, end_time=2.0),
    ]
    return TranscriptInput(dialogue_entries=entries)


@pytest.fixture
def sample_detection():
    spans = [
        EvidenceSpan(dialogue_index=0, text_snippet="He", confidence=0.95),
        EvidenceSpan(dialogue_index=1, text_snippet="he", confidence=0.9),
    ]
    return CharacteristicDetection(
        axis=ProtectedCharacteristic.SEX,
        detected_value="male",
        evidence_spans=spans,
        overall_confidence=0.92,
    )


@pytest.fixture
def sample_axis_change():
    return AxisChange(
        axis=ProtectedCharacteristic.SEX,
        original_value="male",
        target_value="female",
    )


def test_rewriter_initialization(mock_chatbot):
    default_rewriter = CounterfactualRewriter()
    assert default_rewriter.prompt_version == "v1.0"
    assert default_rewriter.model_name == "default_best_llm"

    custom_rewriter = CounterfactualRewriter(chatbot=mock_chatbot, prompt_version="v2.0", model_name="gpt-4")
    assert custom_rewriter.chatbot == mock_chatbot
    assert custom_rewriter.prompt_version == "v2.0"
    assert custom_rewriter.model_name == "gpt-4"


@pytest.mark.asyncio
async def test_rewrite_transcript_applies_transformation_correctly(
    mock_chatbot, sample_transcript, sample_detection, sample_axis_change
):
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    result = await rewriter.rewrite_transcript(sample_transcript, sample_detection, sample_axis_change)

    assert result.original_transcript == sample_transcript
    assert result.rewritten_transcript[0]["text"] == "She is a doctor"
    assert result.rewritten_transcript[1]["text"] == "Yes, she works at the hospital"
    assert result.axis_change == sample_axis_change
    assert set(result.evidence_spans_modified) == {0, 1}
    assert result.prompt_version == "v1.0"


@pytest.mark.asyncio
async def test_rewrite_transcript_tracks_partial_modifications(
    mock_chatbot, sample_transcript, sample_detection, sample_axis_change
):
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, he works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    result = await rewriter.rewrite_transcript(sample_transcript, sample_detection, sample_axis_change)

    assert result.evidence_spans_modified == [0]
    assert result.rewritten_transcript[0]["text"] != sample_transcript.dialogue_entries[0]["text"]
    assert result.rewritten_transcript[1]["text"] == sample_transcript.dialogue_entries[1]["text"]


@pytest.mark.asyncio
async def test_rewrite_transcript_axis_mismatch(mock_chatbot, sample_transcript, sample_detection):
    wrong_axis_change = AxisChange(
        axis=ProtectedCharacteristic.AGE,
        original_value="young",
        target_value="senior",
    )

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    with pytest.raises(ValueError, match="Axis mismatch"):
        await rewriter.rewrite_transcript(sample_transcript, sample_detection, wrong_axis_change)


@pytest.mark.asyncio
async def test_rewrite_transcript_allows_original_value_to_differ_from_detected_value(
    mock_chatbot, sample_transcript, sample_detection
):
    # A change carries a controlled vocabulary value while a detection carries the detector's own
    # phrasing, so a difference between the two must not block the rewrite.
    vocabulary_change = AxisChange(
        axis=ProtectedCharacteristic.SEX,
        original_value="male_participant",
        target_value="female",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    result = await rewriter.rewrite_transcript(sample_transcript, sample_detection, vocabulary_change)

    assert result.rewritten_transcript[0]["text"] == "She is a doctor"


@pytest.mark.asyncio
async def test_rewrite_transcript_text_count_mismatch(
    mock_chatbot, sample_transcript, sample_detection, sample_axis_change
):
    mock_chatbot.chat.return_value = '["Only one text"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    with pytest.raises(ValueError, match="Text count mismatch"):
        await rewriter.rewrite_transcript(sample_transcript, sample_detection, sample_axis_change)


@pytest.mark.asyncio
async def test_rewrite_transcript_rejects_zero_edits(
    mock_chatbot, sample_transcript, sample_detection, sample_axis_change
):
    """A rewrite that returns the original wording has not applied the axis change."""
    mock_chatbot.chat.return_value = '["He is a doctor", "Yes, he works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    with pytest.raises(ValueError, match="Rewrite made no edits"):
        await rewriter.rewrite_transcript(sample_transcript, sample_detection, sample_axis_change)


@pytest.mark.asyncio
async def test_rewrite_transcript_preserves_structure(
    mock_chatbot, sample_transcript, sample_detection, sample_axis_change
):
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    result = await rewriter.rewrite_transcript(sample_transcript, sample_detection, sample_axis_change)

    for _i, (original, rewritten) in enumerate(
        zip(sample_transcript.dialogue_entries, result.rewritten_transcript, strict=False)
    ):
        assert rewritten["speaker"] == original["speaker"]
        assert rewritten["start_time"] == original["start_time"]
        assert rewritten["end_time"] == original["end_time"]

    transcript_with_metadata = TranscriptInput(
        dialogue_entries=[DialogueEntry(speaker="A", text="Hello", start_time=0.0, end_time=1.0)],
        metadata={"source": "test", "version": 1},
    )
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.SEX,
        detected_value="male",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="test", confidence=0.9)],
        overall_confidence=0.9,
    )
    mock_chatbot.chat.return_value = '["Hi"]'
    result = await rewriter.rewrite_transcript(transcript_with_metadata, detection, sample_axis_change)
    assert result.original_transcript.metadata == {"source": "test", "version": 1}


@pytest.mark.asyncio
async def test_rewrite_transcript_no_evidence_spans(mock_chatbot, sample_transcript, sample_axis_change, caplog):
    import logging

    caplog.set_level(logging.INFO)
    detection_no_evidence = CharacteristicDetection(
        axis=ProtectedCharacteristic.SEX,
        detected_value="male",
        evidence_spans=[],
        overall_confidence=0.8,
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection_no_evidence, sample_axis_change)

    assert "No evidence spans provided" in caplog.text


@pytest.mark.asyncio
async def test_rewrite_transcript_builds_prompt_with_evidence_and_instructions(
    mock_chatbot, sample_transcript, sample_detection
):
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.SEX,
        original_value="male",
        target_value="female",
        instructions="Focus on pronouns only",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, sample_detection, axis_change)

    mock_chatbot.chat.assert_called_once()
    call_args = mock_chatbot.chat.call_args
    messages = call_args[1]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    prompt_content = messages[0]["content"]
    assert "Focus on pronouns only" in prompt_content
    assert "He" in prompt_content or "he" in prompt_content


@pytest.mark.asyncio
async def test_sex_prompt_includes_pregnancy_coherence_exception(
    mock_chatbot, sample_transcript, sample_detection, sample_axis_change
):
    """Sex rewrites must document the pregnancy coherence exception in the prompt."""
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, sample_detection, sample_axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "Sex and Pregnancy coherence" in prompt_content
    assert "male participant must not remain described as pregnant" in prompt_content
    assert "do not invent pregnancy or maternity" in prompt_content
