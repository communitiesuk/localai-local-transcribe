from __future__ import annotations

import logging
import uuid
from typing import cast
from uuid import UUID

import mistune
from sqlalchemy.orm import selectinload

from common.convert_american_to_british_spelling import convert_american_to_british_spelling
from common.database.postgres_database import SessionLocal
from common.database.postgres_models import (
    DialogueEntry,
    GuardrailResult,
    Hallucination,
    JobStatus,
    Minute,
    MinuteVersion,
    UserTemplate,
)
from common.format_transcript import transcript_as_speaker_and_utterance
from common.llm.client import FastOrBestLLM, create_default_chatbot
from common.prompts import (
    get_accuracy_check_messages,
    get_ai_edit_initial_messages,
    get_basic_minutes_prompt,
)
from common.services.template_manager import TemplateManager
from common.settings import get_settings
from common.templates.user_template import generate_user_template
from common.types import (
    GuardrailScore,
    LLMHallucination,
    MeetingType,
    MinuteAndHallucinations,
)

settings = get_settings()

logger = logging.getLogger(__name__)

THRESHOLD_FOR_PASSING_ACCURACY_CHECK = settings.GUARDRAIL_THRESHOLD


class MinuteGenerationFailedError(Exception):
    pass


class MinuteHandlerService:
    @staticmethod
    def convert_llm_hallucination_to_db_hallucination(
        llm_hallucination: LLMHallucination, minute_version_id: UUID
    ) -> Hallucination:
        return Hallucination(
            id=uuid.uuid4(),
            hallucination_text=llm_hallucination.hallucination_text,
            hallucination_reason=llm_hallucination.hallucination_reason,
            hallucination_type=llm_hallucination.hallucination_type,
            minute_version_id=minute_version_id,
        )

    @staticmethod
    def save_guardrail_result(
        minute_version_id: UUID,
        score: GuardrailScore,
    ) -> None:
        with SessionLocal() as session:
            passed = score.score >= THRESHOLD_FOR_PASSING_ACCURACY_CHECK

            guardrail_result = GuardrailResult(
                minute_version_id=minute_version_id,
                passed=passed,
                score=score.score,
                reasoning=score.reasoning,
            )
            session.add(guardrail_result)
            session.commit()

    @staticmethod
    def save_guardrail_error(minute_version_id: UUID, error_message: str) -> None:
        with SessionLocal() as session:
            guardrail_result = GuardrailResult(
                minute_version_id=minute_version_id,
                passed=False,
                score=0.0,
                reasoning="System Error: Could not verify accuracy.",
                error=error_message,
            )
            session.add(guardrail_result)
            session.commit()

    @staticmethod
    def update_minute_version(
        minute_version_id: UUID,
        html_content: str | None = None,
        status: JobStatus | None = None,
        error: str | None = None,
        hallucinations: list[LLMHallucination] | None = None,
    ) -> None:
        with SessionLocal() as session:
            minute_version = session.get(MinuteVersion, minute_version_id)
            if not minute_version:
                err_msg = f"MinuteVersion not found for id: {minute_version_id}"
                raise ValueError(err_msg)

            if html_content:
                minute_version.html_content = html_content
            if status:
                minute_version.status = status
            if error:
                minute_version.error = error
            if hallucinations:
                minute_version.hallucinations = [
                    MinuteHandlerService.convert_llm_hallucination_to_db_hallucination(hallucination, minute_version_id)
                    for hallucination in hallucinations
                ]
            session.add(minute_version)
            session.commit()

    @staticmethod
    def _calculate_word_count(transcript: list[DialogueEntry]) -> int:
        count = 0
        for entry in transcript:
            # If it's a dictionary, use ["text"]
            if isinstance(entry, dict):
                count += len(entry.get("text", "").split())
            # If it's a Pydantic object, use .text
            elif hasattr(entry, "text"):
                count += len(entry.text.split())
            # If it's a plain string
            elif isinstance(entry, str):
                count += len(entry.split())
        return count

    @classmethod
    async def get_minute_version(cls, minute_version_id: UUID) -> MinuteVersion:
        with SessionLocal() as session:
            minute_version = session.get(
                MinuteVersion,
                minute_version_id,
                options=[selectinload(MinuteVersion.minute).selectinload(Minute.transcription)],
            )
            if not minute_version:
                msg = f"MinuteVersion not found for id: {minute_version_id}"
                raise ValueError(msg)
            session.expunge(minute_version)
            return minute_version

    @classmethod
    async def get_only_minute_version_for_minute_id(cls, minute_id: UUID) -> MinuteVersion:
        with SessionLocal() as session:
            minute = session.get(
                Minute,
                minute_id,
                options=[selectinload(Minute.minute_versions)],
            )
            if not minute:
                msg = f"Minute not found for minute id: {minute_id}"
                raise ValueError(msg)
            if not minute.minute_versions:
                msg = f"MinuteVersion not found for minute id: {minute_id}"
                raise ValueError(msg)
            if len(minute.minute_versions) != 1:
                msg = (
                    f"More than one MinuteVersions found for minute id: {minute_id}. This function should only be "
                    f"used for the initial generation of a Minute."
                )
                raise ValueError(msg)

            session.expunge(minute)
            return minute.minute_versions[0]

    @classmethod
    async def _run_accuracy_guardrail(
        cls,
        minute_version_id: UUID,
        minute_id: UUID,
        content: str,
        transcript: list[DialogueEntry],
        label: str,
    ) -> None:
        """Helper to run accuracy check and handle result/error logging."""
        word_count = cls._calculate_word_count(transcript)
        if word_count < settings.MIN_WORD_COUNT_FOR_FULL_SUMMARY:
            logger.info(
                "%s: Skipping guardrail check for %s (transcript too short: %d words)", minute_id, label, word_count
            )
            return

        try:
            accuracy_score = await cls.calculate_accuracy_score(
                minute=content,
                transcript=transcript,
            )
            cls.save_guardrail_result(minute_version_id, accuracy_score)
            logger.info("%s: Saved guardrail result for %s: %s", minute_id, label, accuracy_score)
        except Exception as e:
            logger.exception("%s: Failed to run guardrail check for %s", minute_id, label)
            cls.save_guardrail_error(minute_version_id, str(e))

    @classmethod
    async def process_minute_generation_message(cls, minute_version_id: UUID) -> None:
        try:
            minute_version = await cls.get_minute_version(minute_version_id=minute_version_id)
            logger.info("%s: Successfully found MinuteVersion", minute_version.minute_id)
        except Exception as e:
            raise MinuteGenerationFailedError from e
        try:
            dialogue_entries = minute_version.minute.transcription.dialogue_entries
            if not dialogue_entries:
                msg = f"Transcription for minute {minute_version.minute_id} has no dialogue entries"
                raise MinuteGenerationFailedError(msg)

            meeting_type = cls.predict_meeting(dialogue_entries)
            logger.info("%s: Predicted minute version %s", minute_version.minute_id, meeting_type)
            result = await cls.generate_minutes(meeting_type, minute_version.minute)
            html_content = result.text
            hallucinations = result.hallucinations

            await cls._run_accuracy_guardrail(
                minute_version_id=minute_version.id,
                minute_id=minute_version.minute_id,
                content=html_content,
                transcript=dialogue_entries,
                label="generation",
            )

            cls.update_minute_version(
                minute_version.id,
                html_content=html_content,
                hallucinations=hallucinations,
                status=JobStatus.COMPLETED,
            )

        except Exception as e:
            logger.exception(
                "%s: Summary generation failed with %s: %s",
                minute_version.minute_id,
                type(e).__name__,
                e,
            )
            cls.update_minute_version(minute_version.id, status=JobStatus.FAILED, error=str(e))
            raise MinuteGenerationFailedError from e

    @classmethod
    async def process_minute_edit_message(cls, source_minute_version_id: UUID, target_minute_version_id: UUID) -> None:
        try:
            source_minute_version = await cls.get_minute_version(source_minute_version_id)
            target_minute_version = await cls.get_minute_version(target_minute_version_id)
        except Exception as e:
            raise MinuteGenerationFailedError from e

        if (
            target_minute_version.ai_edit_instructions is None
            or str(target_minute_version.ai_edit_instructions).strip() == ""
        ):
            msg = "Target minute does not have AI edit instructions"
            raise MinuteGenerationFailedError(msg)

        try:
            transcript = source_minute_version.minute.transcription.dialogue_entries
            if not transcript:
                msg = "Source minute version has no transcript"
                raise MinuteGenerationFailedError(msg)

            generated = await cls.edit_minutes_with_ai(
                minutes=source_minute_version.html_content,
                edit_instructions=target_minute_version.ai_edit_instructions,
                transcript=transcript,
            )

            await cls._run_accuracy_guardrail(
                minute_version_id=target_minute_version.id,
                minute_id=target_minute_version.minute_id,
                content=generated.text,
                transcript=transcript,
                label="edit",
            )

            cls.update_minute_version(
                minute_version_id=target_minute_version.id,
                status=JobStatus.COMPLETED,
                html_content=generated.text,
                hallucinations=generated.hallucinations,
            )

        except Exception as e:
            cls.update_minute_version(target_minute_version.id, status=JobStatus.FAILED, error=str(e))
            raise MinuteGenerationFailedError from e

    @classmethod
    async def generate_minute_from_user_template(cls, minute: Minute) -> MinuteAndHallucinations:
        with SessionLocal() as session:
            template = session.get(
                UserTemplate, minute.user_template_id, options=[selectinload(UserTemplate.questions)]
            )
        if not template:
            msg = f"No template with id {minute.user_template_id}"
            raise RuntimeError(msg)
        logger.info("%s: Found template id=%s, name=%s", minute.id, template.id, template.name)
        minutes, hallucinations = await generate_user_template(template=template, transcription=minute.transcription)
        return MinuteAndHallucinations(text=minutes, total_claims=0, hallucinations=hallucinations)

    @classmethod
    async def generate_minutes(
        cls,
        meeting_type: MeetingType,
        minute: Minute,
    ) -> MinuteAndHallucinations:
        dialogue_entries = minute.transcription.dialogue_entries
        if not dialogue_entries:
            msg = f"Minute {minute.id} has no dialogue entries"
            raise MinuteGenerationFailedError(msg)

        match meeting_type:
            case MeetingType.too_short:
                generated = cls.handle_bad_transcript(dialogue_entries)
            case MeetingType.short:
                generated = await cls.generate_basic_minutes(dialogue_entries)
            case _:
                generated = await cls.generate_full_minutes(minute)
        html_result = mistune.html(generated.text)
        return MinuteAndHallucinations(
            text=cast(str, html_result), total_claims=generated.total_claims, hallucinations=generated.hallucinations
        )

    @classmethod
    async def generate_full_minutes(cls, minute: Minute) -> MinuteAndHallucinations:
        if minute.user_template_id is not None:
            logger.info(
                "%s: Generating minute from user template user_template_id=%s", minute.id, minute.user_template_id
            )
            generated = await cls.generate_minute_from_user_template(minute)
        else:
            logger.info("%s: Generating minute from default template: %s", minute.id, minute.template_name)
            template = TemplateManager.get_template(minute.template_name)
            generated = await template.generate(minute)
        logger.info("%s: Successfully generated minute", minute.id)
        return MinuteAndHallucinations(
            text=convert_american_to_british_spelling(generated.text),
            total_claims=generated.total_claims,
            hallucinations=generated.hallucinations,
        )

    @classmethod
    def handle_bad_transcript(cls, transcript: list[DialogueEntry]) -> MinuteAndHallucinations:
        return MinuteAndHallucinations(
            text=f"""Short meeting detected. Minutes not available.
         Please try again with a longer meeting. Transcript is: {transcript_as_speaker_and_utterance(transcript)}""",
            total_claims=0,
            hallucinations=[],
        )

    @classmethod
    async def generate_basic_minutes(
        cls,
        transcript: list[DialogueEntry],
    ) -> MinuteAndHallucinations:
        chatbot = create_default_chatbot(FastOrBestLLM.FAST)
        choice = await chatbot.chat(messages=get_basic_minutes_prompt(transcript))
        hallucinations = await chatbot.hallucination_check()
        return MinuteAndHallucinations(text=choice, total_claims=0, hallucinations=hallucinations)

    @classmethod
    def predict_meeting(cls, dialogue_entries: list[DialogueEntry]) -> MeetingType:
        word_count = cls._calculate_word_count(dialogue_entries)
        match word_count:
            case n if n < settings.MIN_WORD_COUNT_FOR_SUMMARY:
                return MeetingType.too_short
            case n if n < settings.MIN_WORD_COUNT_FOR_FULL_SUMMARY:
                return MeetingType.short
            case _:
                return MeetingType.standard

    @classmethod
    async def edit_minutes_with_ai(
        cls,
        minutes: str,
        edit_instructions: str,
        transcript: list[DialogueEntry],
    ) -> MinuteAndHallucinations:
        chatbot = create_default_chatbot(FastOrBestLLM.FAST)
        edited_minutes = await chatbot.chat(
            messages=get_ai_edit_initial_messages(minutes, edit_instructions, transcript)
        )
        edited_minutes = edited_minutes.removeprefix("```html").removesuffix("```")
        hallucinations = await chatbot.hallucination_check()

        return MinuteAndHallucinations(
            text=edited_minutes,
            total_claims=len(hallucinations),
            hallucinations=hallucinations,
        )

    @classmethod
    async def calculate_accuracy_score(
        cls,
        minute: str,
        transcript: list[DialogueEntry],
    ) -> GuardrailScore:
        chatbot = create_default_chatbot(FastOrBestLLM.FAST)
        return await chatbot.structured_chat(
            messages=get_accuracy_check_messages(minute, transcript),
            response_format=GuardrailScore,
        )
