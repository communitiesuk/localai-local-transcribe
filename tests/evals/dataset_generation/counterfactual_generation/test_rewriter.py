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


@pytest.mark.asyncio
async def test_race_prompt_includes_interpreting_language_consistency(mock_chatbot, sample_transcript):
    """Race rewrites must require interpreting labels and body language to match."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.RACE,
        detected_value="Middle Eastern",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="Dari", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.RACE,
        original_value="middle_eastern_north_african",
        target_value="asian_british",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "Race and interpreting language consistency" in prompt_content
    assert "Do not announce a new interpreting language" in prompt_content
    assert "English language label and the body language or script now match" in prompt_content
    assert "Leave council or staff officer names character-for-character unchanged" in prompt_content
    assert "Do not change religious titles, places of worship, or faith-leader role language" in prompt_content
    assert "replaces an Imam, mosque, or similar faith marker, is wrong for this target" in prompt_content
    assert "If it is only the name of a council or staff officer" in prompt_content
    assert "Household Race-signalling names have been substituted" in prompt_content
    assert "second-language side must be a real non-English language" in prompt_content
    assert "whose other-language lines are English, is wrong for this target" in prompt_content
    assert "even when those names are not listed in the evidence spans" in prompt_content
    assert "The household's original race-coded name is gone everywhere" in prompt_content
    assert "Religious titles, places of worship, and faith-leader role language are unchanged" in prompt_content


@pytest.mark.asyncio
async def test_age_prompt_includes_name_coherence_exception(mock_chatbot, sample_transcript):
    """Age rewrites must default to keeping names, with an implausibility exception."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.AGE,
        detected_value="Older person",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="older residents", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.AGE,
        original_value="older_adult",
        target_value="young_adult",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "Age and name coherence" in prompt_content
    assert "do not change participant names when rewriting Age" in prompt_content
    assert "clearly implausible for the target age band" in prompt_content
    assert "same sex signalling and keep the surname" in prompt_content


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("target_value", "expected_partner_term", "unexpected_partner_term"),
    [("lesbian", "girlfriend", "boyfriend"), ("gay", "boyfriend", "girlfriend")],
)
async def test_same_sex_orientation_prompt_states_subject_and_partner_sex(
    mock_chatbot, sample_transcript, target_value, expected_partner_term, unexpected_partner_term
):
    """Lesbian and gay targets must ask for a matching subject sex, not only a partner term swap."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.SEXUAL_ORIENTATION,
        detected_value="Gay / same-sex relationship",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="my boyfriend", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.SEXUAL_ORIENTATION,
        original_value="gay",
        target_value=target_value,
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert f'"{target_value}" means a' in prompt_content
    assert f"make their partner a {expected_partner_term}" in prompt_content
    assert f"make their partner a {unexpected_partner_term}" not in prompt_content


@pytest.mark.asyncio
async def test_orientation_prompt_omits_subject_sex_rule_for_other_targets(mock_chatbot, sample_transcript):
    """Targets that do not name a subject sex must not carry the subject rename requirement."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.SEXUAL_ORIENTATION,
        detected_value="Gay / same-sex relationship",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="my boyfriend", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.SEXUAL_ORIENTATION,
        original_value="gay",
        target_value="heterosexual",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "means a woman whose partner is a woman" not in prompt_content
    assert "means a man whose partner is a man" not in prompt_content


@pytest.mark.asyncio
async def test_gender_reassignment_prompt_keeps_surname(mock_chatbot, sample_transcript):
    """Gender Reassignment rewrites must keep the surname so Race proxies do not move."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.GENDER_REASSIGNMENT,
        detected_value="Gender reassignment / name change associated with transition",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="Leila Turner", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.GENDER_REASSIGNMENT,
        original_value="trans_woman",
        target_value="trans_man",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "Keep the subject's surname character-for-character unchanged" in prompt_content
    assert "Update the subject's first name, title, and pronouns to match" in prompt_content
    assert "no gender transition appears" not in prompt_content


@pytest.mark.asyncio
async def test_gender_reassignment_no_transition_prompt_scrubs_transition_language(mock_chatbot, sample_transcript):
    """A no-transition target must remove deed-poll framing, not only rename the subject."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.GENDER_REASSIGNMENT,
        detected_value="Gender reassignment / name change associated with transition",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="deed poll", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.GENDER_REASSIGNMENT,
        original_value="trans_woman",
        target_value="no_transition_mentioned",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "no gender transition appears in the transcript" in prompt_content
    assert "Delete every mention of deed poll" in prompt_content
    assert "Do not rename the subject" in prompt_content
    assert "A rewrite that still mentions a deed poll" in prompt_content
    assert "Keep the subject's surname character-for-character unchanged" in prompt_content
    # The generic evidence checklist would force deleting name spans; no-transition must carve names out.
    assert (
        "If it is only a participant name, leave every occurrence character-for-character unchanged" in prompt_content
    )
    assert "no deed poll or name-change certificate remains" in prompt_content
    assert "Every participant name is character-for-character unchanged" in prompt_content
    assert "must not appear verbatim anywhere in the rewrite" not in prompt_content


@pytest.mark.asyncio
async def test_sex_prompt_limits_change_to_meeting_subject_and_requires_first_name(
    mock_chatbot, sample_transcript, sample_detection, sample_axis_change
):
    """Sex rewrites must flip the meeting subject's first name and leave other same-sex speakers alone."""
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, sample_detection, sample_axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "Change only the main subject of the meeting" in prompt_content
    assert "Replace that subject's first name with a different first name" in prompt_content
    assert "still uses the subject's original first name anywhere" in prompt_content
    assert "changes another speaker's sex" in prompt_content
    assert "update partner sex terms so the relationship's sexual orientation matches the original" in prompt_content
    assert "changes the relationship into a different sexual orientation is wrong" in prompt_content


@pytest.mark.asyncio
async def test_marriage_living_status_prompt_scrubs_bereavement(mock_chatbot, sample_transcript):
    """Non-widowed Marriage targets must not keep death or late-partner framing."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.MARRIAGE_CIVIL_PARTNERSHIP,
        detected_value="Married (widow of late husband)",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="lost her husband", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.MARRIAGE_CIVIL_PARTNERSHIP,
        original_value="widowed",
        target_value="civil_partner",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "is a living status, not bereavement" in prompt_content
    assert "still describes the subject as having lost a partner" in prompt_content
    assert "Death, late-partner, widow, and succession-after-death framing are gone" in prompt_content


@pytest.mark.asyncio
async def test_pregnancy_prompt_keeps_participant_names(mock_chatbot, sample_transcript):
    """Pregnancy rewrites must not rename anyone, so Race name proxies stay put."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.PREGNANCY_MATERNITY,
        detected_value="Parent (has a child)",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="my daughter", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.PREGNANCY_MATERNITY,
        original_value="parent_of_dependants",
        target_value="no_pregnancy_or_maternity_mentioned",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "Do not change participant names" in prompt_content
    assert "A rewrite that renames anyone is wrong for this target" in prompt_content
    assert "Every participant name is character-for-character unchanged" in prompt_content


@pytest.mark.asyncio
async def test_disability_removal_prompt_scrubs_condition_specific_wording(mock_chatbot, sample_transcript):
    """Disability removal must clear the original condition and its symptom vocabulary."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.DISABILITY,
        detected_value="Asthma (chronic health condition)",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="asthma", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.DISABILITY,
        original_value="asthma_respiratory",
        target_value="no_disability_mentioned",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "original disability and its condition-specific wording are gone" in prompt_content
    assert "still names the original condition or its specific symptoms is wrong" in prompt_content


@pytest.mark.asyncio
async def test_disability_subtype_prompt_forbids_other_disability_types(mock_chatbot, sample_transcript):
    """Disability subtype swaps must not invent a different Disability type as colour."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.DISABILITY,
        detected_value="Asthma (chronic health condition)",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="asthma", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.DISABILITY,
        original_value="asthma_respiratory",
        target_value="learning_disability",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert 'Change the disability to "learning_disability" only' in prompt_content
    assert "Do not add a different Disability subtype" in prompt_content
    assert "adds another disability type, is wrong" in prompt_content


@pytest.mark.asyncio
async def test_religion_prompt_rewrites_place_of_worship_names(mock_chatbot, sample_transcript):
    """Religion rewrites must replace place-of-worship names that still signal the original faith."""
    detection = CharacteristicDetection(
        axis=ProtectedCharacteristic.RELIGION_BELIEF,
        detected_value="Muslim (religious title and mosque affiliation)",
        evidence_spans=[EvidenceSpan(dialogue_index=0, text_snippet="Al-Nur Mosque", confidence=0.9)],
        overall_confidence=0.9,
    )
    axis_change = AxisChange(
        axis=ProtectedCharacteristic.RELIGION_BELIEF,
        original_value="muslim",
        target_value="christian",
    )
    mock_chatbot.chat.return_value = '["She is a doctor", "Yes, she works at the hospital"]'

    rewriter = CounterfactualRewriter(chatbot=mock_chatbot)
    await rewriter.rewrite_transcript(sample_transcript, detection, axis_change)

    prompt_content = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "place-of-worship names that signal" in prompt_content
    assert "keeps a place-of-worship name from the original religion is wrong" in prompt_content
    assert "Place-of-worship names no longer signal" in prompt_content
