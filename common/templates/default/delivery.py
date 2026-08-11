# flake8: noqa: E501
from pydantic import BaseModel, Field

from common.database.postgres_models import DialogueEntry, Minute
from common.llm.client import FastOrBestLLM, create_default_chatbot
from common.prompts import build_summarisation_system_message, get_transcript_messages, render_prompt_template
from common.templates.citations import add_citations_to_minute
from common.templates.types import Template
from common.templates.utils.template_renderer import render_template
from common.types import AgendaUsage, MinuteAndHallucinations


class DeliveryMeetingSection(BaseModel):
    section_name: str = Field(description="Name of the section")
    section_text: str = Field(description="summary of the discussion for the section")
    action_items: list[str] = Field(description="list of action items for the section")


class DeliveryMeetingSections(BaseModel):
    sections_list: list[DeliveryMeetingSection] = Field(
        description="A list of distinct discussion topics or agenda items covered during a formal meeting, such as 'Opening Remarks', 'Previous Actions Review', 'Main Discussion Points', 'Action Items', or 'Closing Summary'. Must be in the order they appear in the transcript.",
        default_factory=list,
    )


class Attendee(BaseModel):
    name: str = Field(description="Name of the attendee")
    role: str = Field(description="Role of the attendee")


class AttendeeList(BaseModel):
    attendees: list[Attendee] = Field(description="List of attendees")


class Delivery(Template):
    name = "Delivery"
    category = "Formal Minutes"
    description = "Formal minutes following the delivery style guide"
    agenda_usage = AgendaUsage.NOT_USED
    # ``generate`` below always runs the citation step, unlike the SimpleTemplate paths where this
    # flag drives it. Declared so the flag is a reliable answer for every template.
    citations_required = True

    @classmethod
    def get_system_message_for_delivery(cls, transcript: list[DialogueEntry]) -> list[dict[str, str]]:
        return [
            build_summarisation_system_message(render_prompt_template("delivery_system.j2")),
            get_transcript_messages(transcript),
        ]

    @classmethod
    def get_messages_for_sections(cls) -> dict[str, str]:
        template = render_template("delivery_style_guide.j2")
        style_guide = template.render()

        return {
            "role": "user",
            "content": render_prompt_template("delivery_sections.j2", style_guide=style_guide),
        }

    @classmethod
    def get_messages_for_attendees(cls) -> dict[str, str]:
        return {"role": "user", "content": render_prompt_template("delivery_attendees.j2")}

    @classmethod
    async def generate(
        cls,
        minute: Minute,
    ) -> MinuteAndHallucinations:
        chatbot = create_default_chatbot(FastOrBestLLM.BEST)
        transcript = minute.transcription.dialogue_entries
        if not transcript:
            msg = f"Minute {minute.id} has no dialogue entries"
            raise ValueError(msg)
        initial_messages = cls.get_system_message_for_delivery(transcript)
        # meeting sections
        initial_messages.append(cls.get_messages_for_sections())
        sections: DeliveryMeetingSections = await chatbot.structured_chat(
            initial_messages, response_format=DeliveryMeetingSections
        )
        # attendees
        attendee_list = await chatbot.structured_chat([cls.get_messages_for_attendees()], response_format=AttendeeList)

        header = "### Attendees:\n"
        for attendee in attendee_list.attendees:
            header += f"{attendee.name}:\t{attendee.role}\n"

        header += "\n\n### Summary of Actions:\n"

        initial_draft = "\n\n### Record of Discussion:\n\n"
        action_index = 1
        for section in sections.sections_list:
            initial_draft += f"### {section.section_name}\n"
            initial_draft += f"{section.section_text}\n"
            for action in section.action_items:
                action_block = f"ACTION {action_index}: {action}\n"
                header += action_block
                initial_draft += action_block
                action_index += 1

        final = header + "\n\n" + initial_draft
        final, total_claims, hallucinations = await add_citations_to_minute(transcript=transcript, initial_draft=final)
        return MinuteAndHallucinations(text=final, total_claims=total_claims, hallucinations=hallucinations)
