from unittest.mock import AsyncMock

import pytest

from evals.dataset_generation.data_for_testing.src.counterfactual_evaluator import (
    AxisTransformation,
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


# --- AxisTransformation ---


def test_axis_transformation_supports_optional_instructions():
    axis = AxisTransformation(axis="Race", original_value="asian", target_value="white_british")
    assert axis.instructions is None

    axis_with_instructions = AxisTransformation(
        axis="Age",
        original_value="older_adults",
        target_value="young_adults",
        instructions="Also replace implicit age signals like 'our age'.",
    )
    assert axis_with_instructions.instructions is not None


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


def _build_structured_chat_responses(axes: list[AxisTransformation], num_rewrites: int = 1) -> list:
    responses = []
    for axis in axes:
        n_axis_chars = sum(
            1 for item in REFERENCE["detected_characteristics"] if item["characteristic"].lower() == axis.axis.lower()
        )
        for _ in range(num_rewrites):
            responses.append(type("C", (), {"score": 4, "explanation": "ok"})())
            for _ in range(n_axis_chars):
                responses.append(type("L", (), {"reasoning": "r", "score": 2, "explanation": "ok"})())
    return responses


@pytest.mark.asyncio
async def test_evaluate_counterfactual_output_has_axes_list():
    mock_chatbot = AsyncMock()
    axes = [AxisTransformation(axis="Race", original_value="asian_participants", target_value="all_white_british")]
    mock_chatbot.structured_chat.side_effect = _build_structured_chat_responses(axes, num_rewrites=1)
    mock_chatbot.chat.return_value = '["Hi Dr. Smith, I feel pressure.", "Hi Sara, let\'s work through this."]'

    report = await evaluate_counterfactual(REFERENCE, DIALOGUE_ENTRIES, mock_chatbot, axes=axes, num_rewrites=1)

    assert "axes" in report
    assert "summary" in report
    assert len(report["axes"]) == 1
    assert report["axes"][0]["axis_change"]["axis"] == "Race"


@pytest.mark.asyncio
async def test_evaluate_counterfactual_does_num_rewrites_per_axis():
    mock_chatbot = AsyncMock()
    axes = [AxisTransformation(axis="Race", original_value="asian_participants", target_value="all_white_british")]
    num_rewrites = 3
    mock_chatbot.structured_chat.side_effect = _build_structured_chat_responses(axes, num_rewrites)
    mock_chatbot.chat.return_value = '["Hi Dr. Smith, I feel pressure.", "Hi Sara, let\'s work through this."]'

    report = await evaluate_counterfactual(
        REFERENCE, DIALOGUE_ENTRIES, mock_chatbot, axes=axes, num_rewrites=num_rewrites
    )

    assert len(report["axes"][0]["rewrites"]) == num_rewrites
    assert mock_chatbot.chat.call_count == num_rewrites


@pytest.mark.asyncio
async def test_evaluate_counterfactual_averages_coherence_across_rewrites():
    mock_chatbot = AsyncMock()
    axes = [AxisTransformation(axis="Race", original_value="asian_participants", target_value="all_white_british")]
    # scores 5, 3 → normalised (5-1)/4=1.0, (3-1)/4=0.5 → average 0.75
    responses = [
        type("C", (), {"score": 5, "explanation": "excellent"})(),
        type("L", (), {"reasoning": "r", "score": 2, "explanation": "ok"})(),
        type("C", (), {"score": 3, "explanation": "ok"})(),
        type("L", (), {"reasoning": "r", "score": 2, "explanation": "ok"})(),
    ]
    mock_chatbot.structured_chat.side_effect = responses
    mock_chatbot.chat.return_value = '["Hi Dr. Smith, I feel pressure.", "Hi Sara, let\'s work through this."]'

    report = await evaluate_counterfactual(REFERENCE, DIALOGUE_ENTRIES, mock_chatbot, axes=axes, num_rewrites=2)

    assert report["axes"][0]["average_coherence"] == 0.75
    assert report["summary"]["average_coherence"] == 0.75


@pytest.mark.asyncio
async def test_evaluate_counterfactual_summary_has_per_axis_stats():
    mock_chatbot = AsyncMock()
    axes = [
        AxisTransformation(axis="Race", original_value="asian_participants", target_value="all_white_british"),
        AxisTransformation(
            axis="Disability", original_value="mental_health_condition", target_value="no_health_issues"
        ),
    ]
    mock_chatbot.structured_chat.side_effect = _build_structured_chat_responses(axes, num_rewrites=2)
    mock_chatbot.chat.return_value = '["Hi Dr. Smith, I feel pressure.", "Hi Sara, let\'s work through this."]'

    report = await evaluate_counterfactual(REFERENCE, DIALOGUE_ENTRIES, mock_chatbot, axes=axes, num_rewrites=2)

    assert report["summary"]["num_axes"] == 2
    assert report["summary"]["num_rewrites_per_axis"] == 2
    assert "successful_axis_rate" in report["summary"]
    assert "average_coherence" in report["summary"]
    assert "average_concealment" in report["summary"]


@pytest.mark.asyncio
async def test_evaluate_counterfactual_successful_axis_rate_when_all_pass():
    mock_chatbot = AsyncMock()
    axes = [AxisTransformation(axis="Race", original_value="asian_participants", target_value="all_white_british")]
    mock_chatbot.structured_chat.side_effect = _build_structured_chat_responses(axes, num_rewrites=2)
    # Both rewrites remove Li Na and Dr. Chen
    mock_chatbot.chat.return_value = '["Hi Dr. Smith, I feel pressure.", "Hi Sara, let\'s work through this."]'

    report = await evaluate_counterfactual(REFERENCE, DIALOGUE_ENTRIES, mock_chatbot, axes=axes, num_rewrites=2)

    assert report["axes"][0]["successful_rewrite_rate"] == 1.0
    assert report["summary"]["successful_axis_rate"] == 1.0


@pytest.mark.asyncio
async def test_evaluate_counterfactual_concealment_checks_only_for_changed_axis():
    mock_chatbot = AsyncMock()
    axes = [AxisTransformation(axis="Race", original_value="asian_participants", target_value="all_white_british")]
    mock_chatbot.structured_chat.side_effect = _build_structured_chat_responses(axes, num_rewrites=1)
    mock_chatbot.chat.return_value = '["Hi Dr. Smith, I feel pressure.", "Hi Sara, let\'s work through this."]'

    report = await evaluate_counterfactual(REFERENCE, DIALOGUE_ENTRIES, mock_chatbot, axes=axes, num_rewrites=1)

    for rewrite in report["axes"][0]["rewrites"]:
        assert all(lc["characteristic"].lower() == "race" for lc in rewrite["concealment_checks"])
        assert not any(lc["characteristic"].lower() == "disability" for lc in rewrite["concealment_checks"])


@pytest.mark.asyncio
async def test_evaluate_counterfactual_empty_axes_returns_empty_report():
    mock_chatbot = AsyncMock()

    report = await evaluate_counterfactual(REFERENCE, DIALOGUE_ENTRIES, mock_chatbot, axes=[], num_rewrites=2)

    assert report["axes"] == []
    assert report["summary"]["num_axes"] == 0
    assert report["summary"]["successful_axis_rate"] == 0.0
    assert report["summary"]["average_coherence"] == 0.0
