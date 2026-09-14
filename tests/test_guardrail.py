from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from common.database.postgres_models import GuardrailResult, JobStatus
from common.services.minute_handler_service import MinuteHandlerService
from common.types import (
    FailureCategory,
    FailureDetail,
    FailureMode,
    GuardrailScore,
    MeetingType,
    MinuteAndHallucinations,
)


@pytest.mark.asyncio
async def test_calculate_accuracy_score():
    # Mock the chatbot and its response
    mock_score = GuardrailScore(score=0.95, reasoning="Excellent summary", categories=[])

    with patch("common.services.minute_handler_service.create_default_chatbot") as mock_create_chatbot:
        mock_chatbot = MagicMock()
        mock_chatbot.structured_chat = AsyncMock(return_value=mock_score)
        mock_create_chatbot.return_value = mock_chatbot

        # Test data
        minute_text = "Meeting summary"
        transcript = [{"speaker": "A", "text": "Hello", "start_time": 0.0, "end_time": 1.0}]

        # Call method
        result = await MinuteHandlerService.calculate_accuracy_score(minute_text, transcript)

        # Assertions
        assert result == mock_score
        assert result.score == 0.95
        assert result.reasoning == "Excellent summary"

        # Verify LLM called correctly
        mock_chatbot.structured_chat.assert_called_once()
        args, kwargs = mock_chatbot.structured_chat.call_args
        assert kwargs["response_format"] == GuardrailScore
        assert len(kwargs["messages"]) == 3
        assert kwargs["messages"][0]["role"] == "system"
        assert "Quality Assurance auditor" in kwargs["messages"][0]["content"]
        assert kwargs["messages"][1]["role"] == "user"
        assert "A: Hello" in kwargs["messages"][1]["content"]
        assert kwargs["messages"][2]["role"] == "user"
        assert minute_text in kwargs["messages"][2]["content"]


@patch("common.services.minute_handler_service.SessionLocal")
def test_save_guardrail_result(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_session

    minute_version_id = "123e4567-e89b-12d3-a456-426614174000"
    score = GuardrailScore(score=0.8, reasoning="Good", categories=[])

    MinuteHandlerService.save_guardrail_result(minute_version_id, score)

    # Verify DB interaction
    mock_session.add.assert_called_once()
    saved_obj = mock_session.add.call_args[0][0]
    assert isinstance(saved_obj, GuardrailResult)
    assert str(saved_obj.minute_version_id) == minute_version_id
    assert saved_obj.score == 0.8
    assert saved_obj.reasoning == "Good"
    assert saved_obj.passed is True
    assert saved_obj.error is None

    mock_session.commit.assert_called_once()


@patch("common.services.minute_handler_service.SessionLocal")
def test_save_guardrail_error(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_session

    minute_version_id = "123e4567-e89b-12d3-a456-426614174000"
    error_msg = "Test error"

    MinuteHandlerService.save_guardrail_error(minute_version_id, error_msg)

    # Verify DB interaction
    mock_session.add.assert_called_once()
    saved_obj = mock_session.add.call_args[0][0]
    assert isinstance(saved_obj, GuardrailResult)
    assert str(saved_obj.minute_version_id) == minute_version_id
    assert saved_obj.passed is False
    assert saved_obj.error == error_msg

    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_minute_generation_runs_guardrails():
    # Setup mocks
    mock_minute_version = MagicMock()
    mock_minute_version.id = uuid4()
    # Provide actual dialogue entries instead of empty list
    mock_minute_version.minute.transcription.dialogue_entries = [
        {"speaker": "A", "text": "word " * 201, "start_time": 0.0, "end_time": 1.0}
    ]

    with (
        patch(
            "common.services.minute_handler_service.MinuteHandlerService.get_minute_version", new_callable=AsyncMock
        ) as mock_get_mv,
        patch("common.services.minute_handler_service.MinuteHandlerService.predict_meeting") as mock_predict,
        patch(
            "common.services.minute_handler_service.MinuteHandlerService.generate_minutes", new_callable=AsyncMock
        ) as mock_gen_minutes,
        patch(
            "common.services.minute_handler_service.MinuteHandlerService.calculate_accuracy_score",
            new_callable=AsyncMock,
        ) as mock_calc_score,
        patch("common.services.minute_handler_service.MinuteHandlerService.save_guardrail_result") as mock_save_result,
        patch("common.services.minute_handler_service.MinuteHandlerService.update_minute_version") as mock_update_mv,
    ):
        mock_get_mv.return_value = mock_minute_version
        mock_predict.return_value = MeetingType.standard
        mock_gen_minutes.return_value = MinuteAndHallucinations(
            text="<html>Minutes</html>",
            total_claims=0,
            hallucinations=[],
        )

        mock_score = GuardrailScore(score=0.9, reasoning="Good", categories=[])
        mock_calc_score.return_value = mock_score

        # Execute
        await MinuteHandlerService.process_minute_generation_message(mock_minute_version.id)

        # Verify
        mock_calc_score.assert_called_once()
        mock_save_result.assert_called_once_with(mock_minute_version.id, mock_score)
        mock_update_mv.assert_called_with(
            mock_minute_version.id, html_content="<html>Minutes</html>", status=JobStatus.COMPLETED
        )


@pytest.mark.asyncio
async def test_process_minute_generation_handles_exception():
    # Setup mocks
    mock_minute_version = MagicMock()
    mock_minute_version.id = uuid4()
    # Provide actual dialogue entries instead of empty list
    mock_minute_version.minute.transcription.dialogue_entries = [
        {"speaker": "A", "text": "word " * 201, "start_time": 0.0, "end_time": 1.0}
    ]

    with (
        patch(
            "common.services.minute_handler_service.MinuteHandlerService.get_minute_version", new_callable=AsyncMock
        ) as mock_get_mv,
        patch("common.services.minute_handler_service.MinuteHandlerService.predict_meeting") as mock_predict,
        patch(
            "common.services.minute_handler_service.MinuteHandlerService.generate_minutes", new_callable=AsyncMock
        ) as mock_gen_minutes,
        patch(
            "common.services.minute_handler_service.MinuteHandlerService.calculate_accuracy_score",
            new_callable=AsyncMock,
        ) as mock_calc_score,
        patch("common.services.minute_handler_service.MinuteHandlerService.save_guardrail_result") as mock_save_result,
        patch("common.services.minute_handler_service.MinuteHandlerService.save_guardrail_error") as mock_save_error,
        patch("common.services.minute_handler_service.MinuteHandlerService.update_minute_version") as mock_update_mv,
    ):
        mock_get_mv.return_value = mock_minute_version
        mock_predict.return_value = MeetingType.standard
        mock_gen_minutes.return_value = MinuteAndHallucinations(
            text="<html>Minutes</html>", total_claims=0, hallucinations=[]
        )

        # Guardrail check raises exception
        mock_calc_score.side_effect = Exception("Guardrail failed")

        # Execute
        await MinuteHandlerService.process_minute_generation_message(mock_minute_version.id)

        # Verify
        mock_calc_score.assert_called_once()
        mock_save_result.assert_not_called()
        mock_save_error.assert_called_once()
        # Should still complete effectively
        mock_update_mv.assert_called_with(
            mock_minute_version.id, html_content="<html>Minutes</html>", status=JobStatus.COMPLETED
        )


def test_guardrail_score_with_failure_categories_round_trips():
    """A GuardrailScore with populated failure details preserves category/mode/explanation."""
    detail = FailureDetail(
        category=FailureCategory.FACTUAL_INTEGRITY,
        mode=FailureMode.INVENTED_DECISION,
        explanation="The minute states the application was approved but no vote occurred in the transcript.",
    )
    score = GuardrailScore(score=0.3, reasoning="Found a fabricated decision", categories=[detail])

    assert score.categories == [detail]
    assert score.categories[0].category == FailureCategory.FACTUAL_INTEGRITY
    assert score.categories[0].mode == FailureMode.INVENTED_DECISION
    assert score.categories[0].explanation


def test_failure_detail_auto_corrects_mismatched_category():
    """A mismatched category is silently corrected to the mode's true owning category."""
    detail = FailureDetail(
        category=FailureCategory.EDIT_SAFETY_AND_INTENT,  # wrong category for this mode
        mode=FailureMode.INVENTED_DECISION,
        explanation="Evidence text",
    )

    assert detail.category == FailureCategory.FACTUAL_INTEGRITY
    assert detail.mode == FailureMode.INVENTED_DECISION


def test_failure_detail_explanation_defaults_to_none():
    """Detailed explanation is optional — omitting it should not block validation."""
    detail = FailureDetail(category=FailureCategory.FACTUAL_INTEGRITY, mode=FailureMode.INVENTED_DECISION)

    assert detail.explanation is None


def test_failure_detail_logs_error_when_mode_has_no_category_mapping(caplog):
    """If a mode has no entry in _CATEGORY_BY_MODE, an error is logged instead of raising."""
    unmapped_mapping = dict(FailureDetail._CATEGORY_BY_MODE)  # noqa: SLF001
    unmapped_mapping[FailureMode.INVENTED_DECISION] = None

    with (
        patch.object(FailureDetail, "_CATEGORY_BY_MODE", unmapped_mapping),
        caplog.at_level("ERROR", logger="common.types"),
    ):
        detail = FailureDetail(
            category=FailureCategory.FACTUAL_INTEGRITY,
            mode=FailureMode.INVENTED_DECISION,
        )

    assert detail.category == FailureCategory.FACTUAL_INTEGRITY
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert "has no known category mapping" in caplog.records[0].message


def test_guardrail_score_logs_warning_when_failing_score_has_no_categories(caplog):
    """A failing score with no failure categories should log a warning, not raise."""
    failing_score = 0.2
    with caplog.at_level("WARNING", logger="common.types"):
        score = GuardrailScore(score=failing_score, reasoning="Inaccurate summary", categories=[])

    assert score.categories == []
    assert caplog.records[0].levelname == "WARNING"
    assert f"GuardrailScore of {failing_score:.2f} is below the guardrail threshold" in caplog.records[0].message
    assert "no failure categories were provided" in caplog.records[0].message


def test_all_failure_modes_are_categorized():
    """Defensive test to ensure that all FailureMode values have a corresponding category mapping."""
    assert set(FailureMode) == set(FailureDetail._CATEGORY_BY_MODE.keys())  # noqa: SLF001
