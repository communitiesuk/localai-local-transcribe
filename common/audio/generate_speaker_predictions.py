import logging

from common.format_transcript import transcript_as_speaker_and_utterance
from common.llm.client import FastOrBestLLM, create_default_chatbot
from common.prompts import build_prompt_injection_aware_system_message, render_prompt_template, wrap_transcript
from common.types import DialogueEntry, SpeakerPredictionOutput

logger = logging.getLogger(__name__)


async def generate_speaker_predictions(dialogue_entries: list[DialogueEntry]) -> dict[str, str]:
    """
    Generate speaker name predictions based on dialogue entries.

    Args:
        dialogue_entries: List of DialogueEntry objects containing speaker and text

    Returns:
        Dictionary mapping original speaker labels to predicted names
    """
    transcript = transcript_as_speaker_and_utterance(dialogue_entries)
    system_message = render_prompt_template("speaker_prediction_system.j2")
    user_message = render_prompt_template("speaker_prediction_user.j2", transcript=wrap_transcript(transcript))

    try:
        chatbot = create_default_chatbot(FastOrBestLLM.FAST)
        messages = [
            build_prompt_injection_aware_system_message(system_message),
            {"role": "user", "content": user_message},
        ]

        speaker_prediction = await chatbot.structured_chat(messages, response_format=SpeakerPredictionOutput)

        if not speaker_prediction.predictions:
            logger.warning("No predictions found, returning original speaker labels")
            return {entry["speaker"]: entry["speaker"] for entry in dialogue_entries}

        return {pred.original_speaker: pred.predicted_name for pred in speaker_prediction.predictions}
    except Exception as e:  # noqa: BLE001 # flagged by ruff - investigate when we have time.
        error_message = str(e)
        # Check for content filter errors from Azure OpenAI
        if any(
            term in error_message.lower()
            for term in [
                "content_filter",
                "content filter",
                "content management policy",
                "filtered",
                "policy violation",
            ]
        ):
            # Log the content filter error but continue with original speaker labels
            logger.warning(
                "Content filter detected in transcript. Continuing with original speaker labels: %s",
                type(e).__name__,
            )

            # Return original speaker labels
            return {entry["speaker"]: entry["speaker"] for entry in dialogue_entries}
        else:
            # For other errors, log and return original speaker labels
            logger.error("Error predicting speaker names: %s", type(e).__name__)
            return {entry["speaker"]: entry["speaker"] for entry in dialogue_entries}
