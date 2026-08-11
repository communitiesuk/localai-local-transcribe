import markdownify

from common.database.postgres_models import TemplateType, Transcription, UserTemplate
from common.format_transcript import transcript_as_speaker_and_utterance
from common.llm.client import FastOrBestLLM, create_default_chatbot
from common.prompts import (
    build_summarisation_system_message,
    get_transcript_messages,
    render_prompt_template,
    wrap_custom_template,
    wrap_transcript,
)
from common.types import MinuteAndHallucinations


async def generate_user_template(template: UserTemplate, transcription: Transcription) -> MinuteAndHallucinations:
    if template.type == TemplateType.DOCUMENT:
        markdown_template = markdownify.markdownify(template.content, heading_style=markdownify.ATX)

        messages = [
            build_summarisation_system_message(render_prompt_template("user_template_document_system.j2")),
            {
                "role": "user",
                "content": render_prompt_template(
                    "user_template_document_input.j2",
                    custom_template=wrap_custom_template(markdown_template),
                    date=transcription.created_datetime.strftime("%A %d %B %Y %H:%M:%S"),
                ),
            },
            get_transcript_messages(transcription.dialogue_entries or []),
        ]
        chatbot = create_default_chatbot(FastOrBestLLM.BEST)
        response = await chatbot.chat(messages)
        return MinuteAndHallucinations(text=response, total_claims=0, hallucinations=[])
    else:
        qa_pairs: list[tuple[str, str]] = []
        for question in template.questions:
            chatbot = create_default_chatbot(FastOrBestLLM.FAST)
            if len(qa_pairs) > 0:
                previous_questions = "\n\n".join(f"## {q}\n{a}" for (q, a) in qa_pairs)
            else:
                previous_questions = render_prompt_template("user_template_no_previous_questions.j2").rstrip()

            custom_template = render_prompt_template(
                "user_template_form_custom_template.j2",
                style_guide=template.content,
                current_question=question.title,
                question_description=question.description.strip(),
            )

            messages = [
                build_summarisation_system_message(render_prompt_template("user_template_form_system.j2")),
                {
                    "role": "user",
                    "content": render_prompt_template(
                        "user_template_form_input.j2",
                        transcript=wrap_transcript(
                            transcript_as_speaker_and_utterance(transcription.dialogue_entries or [])
                        ),
                        custom_template=wrap_custom_template(custom_template),
                        previous_questions=previous_questions,
                    ),
                },
            ]
            resp = await chatbot.chat(messages)
            qa_pairs.append((question.title, resp))

        minute = "\n\n".join(f"## {q}\n{a}" for (q, a) in qa_pairs)

        return MinuteAndHallucinations(text=minute, total_claims=0, hallucinations=[])
