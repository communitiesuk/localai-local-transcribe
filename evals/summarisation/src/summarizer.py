from __future__ import annotations

import uuid
from datetime import UTC, datetime

from common.database.postgres_models import DialogueEntry, Minute, TemplateType, Transcription, UserTemplate
from common.services.minute_handler_service import MinuteHandlerService
from common.services.template_manager import TemplateManager
from common.templates.user_template import generate_user_template
from common.types import MinuteAndHallucinations


async def generate_summary(
    dialogue_entries: list[DialogueEntry],
    template_name: str | None = None,
) -> MinuteAndHallucinations:
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

        return await template.generate(mock_minute)
    else:
        return await MinuteHandlerService.generate_basic_minutes(dialogue_entries)


async def generate_summary_from_custom_template(
    dialogue_entries: list[DialogueEntry],
    template_content: str,
) -> MinuteAndHallucinations:
    """Summarise ``dialogue_entries`` using a user-supplied custom DOCUMENT template.

    This drives the same production path as a user pasting their own template into the app
    (``common.templates.user_template.generate_user_template``): the raw ``template_content`` is
    embedded verbatim into the summariser's system prompt. It is the injection surface exercised by
    the template-vector security eval — off-policy instructions placed in the custom template must
    not redirect the model away from summarisation.
    """
    transcription = Transcription(
        id=uuid.uuid4(),
        dialogue_entries=dialogue_entries,
        text="",
        status="COMPLETED",
        created_datetime=datetime.now(UTC),
    )
    user_template = UserTemplate(
        id=uuid.uuid4(),
        name="custom-security-eval",
        content=template_content,
        type=TemplateType.DOCUMENT,
    )
    return await generate_user_template(user_template, transcription)
