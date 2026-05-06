from unittest.mock import AsyncMock

import pytest

from evals.dataset_generation.data_for_testing.src.counterfactual_evaluator import (
    AxesResponse,
    AxisTransformation,
    _propose_axes,
    _rewrite_transcript,
    check_removals,
    evaluate_counterfactual,
    extract_characteristics,
    extract_span_contexts,
)

REFERENCE = {
    "detected_characteristics": [
        {
            "characteristic": "Race",
            "attribute_value": "Asian",
            "evidence_spans": [
                {"text": "Li Na"},
                {"text": "Li Na"},
                {"text": "Dr. Chen"},
            ],
        },
        {
            "characteristic": "Disability",
            "attribute_value": "Mental health condition",
            "evidence_spans": [{"text": "overwhelming"}],
        },
    ]
}

DIALOGUE_ENTRIES = [
    {"speaker": "1", "text": "Hi Dr. Chen, I feel overwhelming pressure."},
    {"speaker": "2", "text": "Hi Li Na, let's work through this."},
]


# --- extract_span_contexts ---


def test_extract_span_contexts_deduplicates_within_same_characteristic():
    # "Li Na" appears twice under the same Race/Asian characteristic — should appear once
    result = extract_span_contexts(REFERENCE)
    texts = [s["text"] for s in result]
    assert texts.count("Li Na") == 1
    assert "Dr. Chen" in texts
    assert "overwhelming" in texts


def test_extract_span_contexts_preserves_category_and_value():
    result = extract_span_contexts(REFERENCE)
    race_span = next(s for s in result if s["text"] == "Li Na")
    assert race_span["category"] == "Race"
    assert race_span["value"] == "Asian"


def test_extract_span_contexts_same_text_multiple_characteristics():
    # "Margaret" signals both Sex (Female) and Race (White British) — must appear for each
    reference = {
        "detected_characteristics": [
            {
                "characteristic": "Sex",
                "attribute_value": "Female",
                "evidence_spans": [{"text": "Margaret"}],
            },
            {
                "characteristic": "Race",
                "attribute_value": "White British",
                "evidence_spans": [{"text": "Margaret"}],
            },
        ]
    }
    result = extract_span_contexts(reference)
    entries = [(s["text"], s["category"]) for s in result]
    assert ("Margaret", "Sex") in entries
    assert ("Margaret", "Race") in entries
    assert len(result) == 2


# --- extract_characteristics ---


def test_extract_characteristics_returns_unique_pairs():
    result = extract_characteristics(REFERENCE)
    assert ("Race", "Asian") in result
    assert ("Disability", "Mental health condition") in result
    assert len(result) == 2


# --- check_removals ---


def test_check_removals_detects_remaining_values():
    result = check_removals("Hello Li Na, how are you?", ["Li Na", "Dr. Chen"])
    li_na = next(r for r in result if r["original_value"] == "Li Na")
    dr_chen = next(r for r in result if r["original_value"] == "Dr. Chen")
    assert li_na["found_in_rewrite"] is True
    assert li_na["occurrences"] == 1
    assert dr_chen["found_in_rewrite"] is False


def test_check_removals_word_boundary_does_not_match_substring():
    # "Na" must not match inside "Natural" — README documents \b boundary behaviour
    result = check_removals("Natural language processing is fascinating", ["Na"])
    na = next(r for r in result if r["original_value"] == "Na")
    assert na["found_in_rewrite"] is False
    assert na["occurrences"] == 0


def test_check_removals_word_boundary_matches_standalone():
    result = check_removals("Hi Na, how are you?", ["Na"])
    na = next(r for r in result if r["original_value"] == "Na")
    assert na["found_in_rewrite"] is True
    assert na["occurrences"] == 1


# --- _propose_axes ---


@pytest.mark.asyncio
async def test_propose_axes_returns_axis_transformations():
    mock_chatbot = AsyncMock()
    mock_chatbot.structured_chat.return_value = AxesResponse(
        axes=[
            AxisTransformation(
                axis="Race",
                original_value="asian_participants",
                target_value="all_white_british",
            )
        ]
    )
    entries = [{"text": "Li Na", "value": "Asian", "category": "Race"}]

    result = await _propose_axes(mock_chatbot, entries, n=1)

    assert len(result) == 1
    assert result[0].axis == "Race"
    assert result[0].target_value == "all_white_british"
    mock_chatbot.clear_history.assert_called_once()


# --- _rewrite_transcript ---


@pytest.mark.asyncio
async def test_rewrite_transcript_returns_parsed_texts():
    mock_chatbot = AsyncMock()
    mock_chatbot.chat.return_value = '["Hello Dr. Smith.", "Hi Sara, let\'s work through this."]'
    axis_transform = AxisTransformation(
        axis="Race",
        original_value="asian_participants",
        target_value="all_white_british",
    )

    result = await _rewrite_transcript(mock_chatbot, ["Hi Dr. Chen.", "Hi Li Na."], axis_transform, [])

    assert result == ["Hello Dr. Smith.", "Hi Sara, let's work through this."]
    mock_chatbot.clear_history.assert_called_once()


@pytest.mark.asyncio
async def test_rewrite_transcript_only_passes_axis_spans_to_prompt():
    mock_chatbot = AsyncMock()
    mock_chatbot.chat.return_value = '["rewritten"]'
    axis_transform = AxisTransformation(
        axis="Race",
        original_value="asian_participants",
        target_value="all_white_british",
    )
    all_spans = [
        {"text": "Li Na", "category": "Race", "value": "Asian"},
        {"text": "overwhelming", "category": "Disability", "value": "Mental health condition"},
    ]

    await _rewrite_transcript(mock_chatbot, ["original"], axis_transform, all_spans)

    prompt_text = mock_chatbot.chat.call_args[1]["messages"][0]["content"]
    assert "Li Na" in prompt_text
    assert "overwhelming" not in prompt_text


# --- evaluate_counterfactual ---


def _mock_side_effects(axes: list[AxisTransformation]) -> list:
    """Build structured_chat side-effects for axes × characteristics."""
    n_chars = len(REFERENCE["detected_characteristics"])
    responses = [AxesResponse(axes=axes)]
    for _ in axes:
        responses.append(type("C", (), {"score": 4, "explanation": "ok"})())
        for _ in range(n_chars):
            responses.append(type("L", (), {"reasoning": "r", "score": 2, "explanation": "ok"})())
    return responses


@pytest.mark.asyncio
async def test_evaluate_counterfactual_produces_one_rewrite_per_proposed_axis():
    mock_chatbot = AsyncMock()
    axes = [
        AxisTransformation(axis="Race", original_value="asian_participants", target_value="all_white_british"),
        AxisTransformation(
            axis="Disability", original_value="mental_health_condition", target_value="no_health_issues"
        ),
    ]
    mock_chatbot.structured_chat.side_effect = _mock_side_effects(axes)
    mock_chatbot.chat.return_value = '["Hi Dr. Smith, I feel pressure.", "Hi Sara, let\'s work through this."]'

    report = await evaluate_counterfactual(REFERENCE, DIALOGUE_ENTRIES, mock_chatbot, num_alternatives=2)

    assert len(report["rewrites"]) == 2
    assert report["rewrites"][0]["axis_change"]["axis"] == "Race"
    assert report["rewrites"][1]["axis_change"]["axis"] == "Disability"
    assert "replacements" not in report["rewrites"][0]


@pytest.mark.asyncio
async def test_evaluate_counterfactual_summary_successful_rate():
    """successful_rewrite_rate = 1.0 when the LLM removes the target evidence spans."""
    mock_chatbot = AsyncMock()
    axes = [AxisTransformation(axis="Race", original_value="asian_participants", target_value="all_white_british")]
    mock_chatbot.structured_chat.side_effect = _mock_side_effects(axes)
    # Rewrite removes both "Li Na" and "Dr. Chen"
    mock_chatbot.chat.return_value = '["Hi Dr. Smith, I feel pressure.", "Hi Sara, let\'s work through this."]'

    report = await evaluate_counterfactual(REFERENCE, DIALOGUE_ENTRIES, mock_chatbot, num_alternatives=1)

    assert report["summary"]["successful_rewrite_rate"] == 1.0
    assert report["summary"]["num_rewrites"] == 1
    assert report["rewrites"][0]["all_values_removed"] is True
    assert report["rewrites"][0]["unexpected_edits"] == []


@pytest.mark.asyncio
async def test_evaluate_counterfactual_empty_axes_returns_empty_report():
    mock_chatbot = AsyncMock()
    mock_chatbot.structured_chat.return_value = AxesResponse(axes=[])

    report = await evaluate_counterfactual(REFERENCE, DIALOGUE_ENTRIES, mock_chatbot)

    assert report["rewrites"] == []
    assert report["summary"]["num_rewrites"] == 0
    assert report["summary"]["successful_rewrite_rate"] == 0.0
    assert report["summary"]["average_coherence"] == 0.0
