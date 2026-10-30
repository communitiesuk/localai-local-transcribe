import datetime as dt
import html
import re
from typing import TypedDict
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import literal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select

from backend.api.dependencies import UserDep
from backend.api.dependencies.get_session import SQLSessionDep
from common.database.postgres_models import TemplateQuestion, TemplateType, UserTemplate
from common.prompts import PROMPT_INJECTION_INSTRUCTIONS
from common.services.template_manager import TemplateManager, TemplateNotFoundError
from common.settings import get_settings
from common.templates.name_normalisation import (
    TEMPLATE_NAME_TRIM_CHARS,
    USER_TEMPLATE_NORMALISED_NAME_UNIQUE_INDEX,
    normalise_template_name,
)
from common.templates.types import Template
from common.types import (
    CreateUserTemplateRequest,
    DuplicateTemplateResponse,
    PatchUserTemplateRequest,
    Question,
    TemplateMetadata,
    TemplateResponse,
)

templates_router = APIRouter(tags=["Templates"])
all_template_metadata = TemplateManager.get_template_metadata()
beta_templates = get_settings().BETA_TEMPLATE_NAMES
ga_only_template_metadata = [template for template in all_template_metadata if template.name not in beta_templates]

TEMPLATE_TITLE_CONFLICT_DETAIL = "A template with this title already exists"
MAX_DUPLICATE_NAME_ATTEMPTS = 10


def is_template_name_unique_violation(error: IntegrityError) -> bool:
    return USER_TEMPLATE_NORMALISED_NAME_UNIQUE_INDEX in str(error.orig)


async def commit_or_raise_template_name_conflict(session: SQLSessionDep) -> None:
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        if is_template_name_unique_violation(error):
            raise HTTPException(status_code=409, detail=TEMPLATE_TITLE_CONFLICT_DETAIL) from error
        raise


@templates_router.get("/templates")
def get_templates(user: UserDep) -> list[TemplateMetadata]:  # noqa: ARG001
    """Get metadata for all templates."""
    # currently we have no beta templates. Uncomment this code to enable this feature
    # if posthog_client and posthog_client.get_feature_flag("beta-templates", user.email):
    #     return all_template_metadata
    # else:
    #     return ga_only_template_metadata
    return ga_only_template_metadata


@templates_router.get("/user-templates")
async def get_user_templates(user: UserDep, session: SQLSessionDep) -> list[TemplateResponse]:
    templates = (
        await session.exec(
            select(UserTemplate)
            .where(UserTemplate.user_id == user.id)
            .order_by(col(UserTemplate.updated_datetime).desc())
        )
    ).all()

    return [
        TemplateResponse(
            id=template.id,
            updated_datetime=template.updated_datetime,
            name=template.name,
            content=template.content,
            heading=template.heading,
            description=template.description,
            type=template.type,
            questions=None,
        )
        for template in templates
    ]


@templates_router.get("/user-templates/{template_id}")
async def get_user_template(user: UserDep, session: SQLSessionDep, template_id: UUID) -> TemplateResponse:
    template = (
        await session.exec(
            select(UserTemplate)
            .where(UserTemplate.id == template_id, UserTemplate.user_id == user.id)
            .options(selectinload(UserTemplate.questions))
        )
    ).first()

    if not template:
        raise HTTPException(404)

    return TemplateResponse(
        id=template.id,
        name=template.name,
        updated_datetime=template.updated_datetime,
        content=template.content,
        heading=template.heading,
        description=template.description,
        type=template.type,
        questions=None
        if template.type == TemplateType.DOCUMENT
        else [
            Question(
                id=question.id,
                title=question.title,
                description=question.description,
                format_instructions=question.format_instructions,
                position=question.position,
            )
            for question in template.questions
        ],
    )


@templates_router.post("/user-templates")
async def create_user_template(user: UserDep, session: SQLSessionDep, request: CreateUserTemplateRequest) -> None:
    existing_template = (
        await session.exec(
            select(UserTemplate).where(
                UserTemplate.user_id == user.id,
                func.lower(func.btrim(col(UserTemplate.name), literal(TEMPLATE_NAME_TRIM_CHARS)))
                == normalise_template_name(request.name),
            )
        )
    ).first()
    if existing_template:
        raise HTTPException(status_code=409, detail=TEMPLATE_TITLE_CONFLICT_DETAIL)

    template = UserTemplate(
        name=request.name,
        content=request.content,
        heading=request.heading,
        description=request.description,
        user_id=user.id,
        type=request.type,
        questions=[
            TemplateQuestion(
                position=question.position,
                title=question.title,
                description=question.description,
                format_instructions=question.format_instructions,
            )
            for question in (request.questions or [])
        ],
    )

    session.add(template)
    await commit_or_raise_template_name_conflict(session)


@templates_router.patch("/user-templates/{template_id}")
async def edit_user_template(
    user: UserDep, session: SQLSessionDep, template_id: UUID, request: PatchUserTemplateRequest
) -> None:
    template = (
        await session.exec(select(UserTemplate).where(UserTemplate.id == template_id, UserTemplate.user_id == user.id))
    ).first()

    if not template:
        raise HTTPException(404)

    if request.name is not None:
        conflicting_template = (
            await session.exec(
                select(UserTemplate).where(
                    UserTemplate.user_id == user.id,
                    UserTemplate.id != template_id,
                    func.lower(func.btrim(col(UserTemplate.name), literal(TEMPLATE_NAME_TRIM_CHARS)))
                    == normalise_template_name(request.name),
                )
            )
        ).first()
        if conflicting_template:
            raise HTTPException(status_code=409, detail=TEMPLATE_TITLE_CONFLICT_DETAIL)

        template.name = request.name

    if request.content is not None:
        template.content = request.content
    if request.heading is not None:
        template.heading = request.heading
    if request.description is not None:
        template.description = request.description
    if request.questions is not None:
        questions = list(
            (await session.exec(select(TemplateQuestion).where(TemplateQuestion.user_template_id == template_id))).all()
        )
        for question in request.questions:
            if isinstance(question, Question):
                existing_idx = next((i for i, q in enumerate(questions) if q.id == question.id), None)
                if existing_idx is not None:
                    existing = questions.pop(existing_idx)
                    existing.title = question.title
                    existing.description = question.description
                    existing.format_instructions = question.format_instructions
                    existing.position = question.position
                    continue

            session.add(
                TemplateQuestion(
                    user_template_id=template_id,
                    position=question.position,
                    title=question.title,
                    description=question.description,
                    format_instructions=question.format_instructions,
                )
            )
        for remaining_question in questions:
            await session.delete(remaining_question)

    template.updated_datetime = dt.datetime.now(tz=dt.UTC)
    await commit_or_raise_template_name_conflict(session)


@templates_router.delete("/user-templates/{template_id}")
async def delete_user_template(user: UserDep, session: SQLSessionDep, template_id: UUID) -> None:
    template = (
        await session.exec(select(UserTemplate).where(UserTemplate.id == template_id, UserTemplate.user_id == user.id))
    ).first()

    if not template:
        raise HTTPException(404)

    await session.delete(template)
    await session.commit()


async def next_unique_template_name(session: SQLSessionDep, user_id: UUID, base_name: str) -> str:
    existing_templates = (await session.exec(select(UserTemplate.name).where(UserTemplate.user_id == user_id))).all()
    existing_names = {normalise_template_name(name) for name in existing_templates}

    copy_base = f"{base_name} (Copy)"
    if normalise_template_name(copy_base) not in existing_names:
        return copy_base

    counter = 2
    while True:
        new_name = f"{base_name} (Copy {counter})"
        if normalise_template_name(new_name) not in existing_names:
            return new_name
        counter += 1


class TemplateQuestionCopy(TypedDict):
    position: int
    title: str
    description: str
    format_instructions: str


async def duplicate_template(
    session: SQLSessionDep,
    user_id: UUID,
    base_name: str,
    description: str,
    content: str,
    heading: str,
    template_type: TemplateType,
    questions: list[TemplateQuestion],
) -> DuplicateTemplateResponse:
    # Copy questions before entering loop as rollback can interfere with ORM relationship values
    question_copies: list[TemplateQuestionCopy] = [
        {
            "position": question.position,
            "title": question.title,
            "description": question.description,
            "format_instructions": question.format_instructions,
        }
        for question in questions
    ]

    for _ in range(MAX_DUPLICATE_NAME_ATTEMPTS):
        template = UserTemplate(
            user_id=user_id,
            name=await next_unique_template_name(session, user_id, base_name),
            description=description,
            content=content,
            heading=heading,
            type=template_type,
            questions=[
                TemplateQuestion(
                    position=question["position"],
                    title=question["title"],
                    description=question["description"],
                    format_instructions=question["format_instructions"],
                )
                for question in question_copies
            ],
        )

        session.add(template)
        try:
            await session.commit()
        except IntegrityError as error:
            await session.rollback()
            if is_template_name_unique_violation(error):
                continue
            raise

        return DuplicateTemplateResponse(id=template.id, name=template.name)

    raise HTTPException(status_code=409, detail=TEMPLATE_TITLE_CONFLICT_DETAIL)


@templates_router.post("/user-templates/{template_id}/duplicate")
async def duplicate_user_template(
    user: UserDep, session: SQLSessionDep, template_id: UUID
) -> DuplicateTemplateResponse:
    original_template = (
        await session.exec(
            select(UserTemplate)
            .where(UserTemplate.id == template_id, UserTemplate.user_id == user.id)
            .options(selectinload(UserTemplate.questions))
        )
    ).first()

    if not original_template:
        raise HTTPException(404)

    return await duplicate_template(
        session=session,
        user_id=user.id,
        base_name=original_template.name,
        description=original_template.description,
        content=original_template.content,
        heading=original_template.heading,
        template_type=original_template.type,
        questions=original_template.questions,
    )


@templates_router.post("/templates/{template_name}/duplicate")
async def duplicate_default_template(
    user: UserDep, session: SQLSessionDep, template_name: str
) -> DuplicateTemplateResponse:
    template_metadata = next(
        (template for template in get_templates(user) if template_name in {template.id, template.name}),
        None,
    )
    if template_metadata is None:
        raise HTTPException(404)

    try:
        original_template = TemplateManager.get_template(template_metadata.name)
    except TemplateNotFoundError as e:
        raise HTTPException(404) from e

    return await duplicate_template(
        session=session,
        user_id=user.id,
        base_name=original_template.name,
        description=original_template.description,
        content=get_default_template_content(original_template),
        heading=original_template.name,
        template_type=TemplateType.DOCUMENT,
        questions=[],
    )


def get_default_template_content(default_template: type[Template]) -> str:
    editable_content = getattr(default_template, "editable_content", None)
    if isinstance(editable_content, str):
        return editable_content

    prompt = getattr(default_template, "prompt", None)
    if not callable(prompt):
        return default_template.description

    messages = prompt([], None)
    content = next(
        (message["content"] for message in messages if message.get("role") == "system"),
        default_template.description,
    )
    return _plain_text_to_editable_html(content.removeprefix(PROMPT_INJECTION_INSTRUCTIONS).strip())


def _plain_text_to_editable_html(content: str) -> str:
    blocks: list[str] = []
    list_items: list[str] = []

    def flush_list() -> None:
        if not list_items:
            return
        blocks.append("<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>")
        list_items.clear()

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            flush_list()
            continue

        heading_match = re.fullmatch(r"(#{1,6})\s+(.+)", line)
        if heading_match:
            flush_list()
            level = len(heading_match.group(1))
            blocks.append(f"<h{level}>{html.escape(heading_match.group(2))}</h{level}>")
            continue

        list_match = re.fullmatch(r"[-*]\s+(.+)", line)
        if list_match:
            list_items.append(html.escape(list_match.group(1)))
            continue

        flush_list()
        blocks.append(f"<p>{html.escape(line)}</p>")

    flush_list()
    return "\n".join(blocks) if blocks else "<p></p>"
