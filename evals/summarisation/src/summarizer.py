from __future__ import annotations

import uuid

from common.database.postgres_models import DialogueEntry, Minute, Transcription
from common.services.minute_handler_service import MinuteHandlerService
from common.services.template_manager import TemplateManager
from common.types import LLMHallucination


async def generate_summary(
    dialogue_entries: list[DialogueEntry],
    template_name: str | None = None,
) -> tuple[str, int, list[LLMHallucination]]:
    """
    Generates a summary from dialogue entries using specified template or basic minutes.

    Returns the summary text, total claims extracted (0 if no citation pipeline ran),
    and any hallucinations detected during generation (including uncited claims).
    """
    if template_name:
        template = TemplateManager.get_template(template_name)

        mock_transcription = Transcription(
            id=uuid.uuid4(),
            dialogue_entries=dialogue_entries,
            text="",
            status="COMPLETED",
        )
        mock_minute = Minute(
            id=uuid.uuid4(),
            transcription_id=mock_transcription.id,
            template_name=template_name,
        )
        mock_minute.transcription = mock_transcription

        result, total_claims, hallucinations = await template.generate(mock_minute)
        return result, total_claims, hallucinations
    else:
        result, total_claims, hallucinations = await MinuteHandlerService.generate_basic_minutes(dialogue_entries)
        return result, total_claims, hallucinations
