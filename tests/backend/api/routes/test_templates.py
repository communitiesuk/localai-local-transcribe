# ruff: noqa: ARG001
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from backend.api.routes.templates import (
    create_user_template,
    delete_user_template,
    duplicate_user_template,
    edit_user_template,
    get_user_template,
    get_user_templates,
)
from common.services.template_manager import TemplateManager
from common.types import Question
from tests.utils import get_test_client


@pytest.mark.asyncio
async def test_get_templates_success(override_user, override_session):
    async with get_test_client() as ac:
        response = await ac.get("/templates")
        assert response.status_code == 200
        assert len(response.json()) == len(TemplateManager.templates)


@pytest.mark.asyncio
async def test_get_user_templates_success(mock_session, mock_user, mock_user_template):
    exec_result = Mock()
    exec_result.all.return_value = [mock_user_template]
    mock_session.exec.return_value = exec_result

    result = await get_user_templates(mock_user, mock_session)
    assert len(result) == 1
    assert result[0].id == mock_user_template.id
    assert result[0].name == mock_user_template.name


@pytest.mark.asyncio
async def test_get_user_template_success(mock_session, mock_user, mock_user_template):
    exec_result = Mock()
    exec_result.first.return_value = mock_user_template
    mock_session.exec.return_value = exec_result

    response = await get_user_template(mock_user, mock_session, mock_user_template.id)

    assert response.id == mock_user_template.id
    assert response.type == mock_user_template.type


@pytest.mark.asyncio
async def test_get_user_template_not_found(mock_session, mock_user):
    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await get_user_template(mock_user, mock_session, uuid.uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_user_template_calls_add_and_commit(
    mock_session, mock_user, mock_user_template, mock_request, monkeypatch
):
    monkeypatch.setattr("backend.api.routes.templates.UserTemplate", lambda **_: mock_user_template)

    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result

    await create_user_template(mock_user, mock_session, mock_request)
    mock_session.add.assert_called_once_with(mock_user_template)
    mock_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_create_user_template_has_right_details(mock_session, mock_user, mock_request):
    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result

    await create_user_template(mock_user, mock_session, mock_request)
    template = mock_session.add.call_args.args[0]
    assert template.name == mock_request.name
    assert template.content == mock_request.content
    assert template.heading == mock_request.heading
    assert template.description == mock_request.description
    assert template.type == mock_request.type


@pytest.mark.asyncio
async def test_create_user_template_duplicate_title(mock_session, mock_user, mock_user_template, mock_request):
    exec_result = Mock()
    exec_result.first.return_value = mock_user_template
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await create_user_template(mock_user, mock_session, mock_request)

    assert exc_info.value.status_code == 409
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_user_template_success(mock_session, mock_user, mock_user_template, mock_request):
    exec_result = Mock()
    exec_result.first.return_value = mock_user_template

    exec_q = Mock()
    exec_q.all.return_value = []

    mock_session.exec.side_effect = [exec_result, exec_q]

    original_datetime = mock_user_template.updated_datetime

    await edit_user_template(mock_user, mock_session, mock_user_template.id, mock_request)

    mock_session.add.assert_called()
    mock_session.commit.assert_awaited()

    assert mock_user_template.name == mock_request.name
    assert mock_user_template.content == mock_request.content

    added_question = mock_session.add.call_args.args[0]
    assert added_question.user_template_id == mock_user_template.id
    assert added_question.position == mock_request.questions[0].position
    assert added_question.title == mock_request.questions[0].title

    mock_session.delete.assert_not_called()

    assert mock_user_template.updated_datetime > original_datetime


@pytest.mark.asyncio
async def test_edit_user_template_not_found(mock_session, mock_user, mock_user_template, mock_request):
    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.side_effect = [exec_result]

    mock_request.content = None
    mock_request.description = None

    with pytest.raises(HTTPException) as exc_info:
        await edit_user_template(mock_user, mock_session, mock_user_template.id, mock_request)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_template_success(mock_session, mock_user, mock_user_template):
    exec_result = Mock()
    exec_result.first.return_value = mock_user_template
    mock_session.exec.return_value = exec_result

    await delete_user_template(mock_user, mock_session, mock_user_template.id)

    mock_session.delete.assert_awaited()
    mock_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_user_template_not_found(mock_session, mock_user):
    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_user_template(mock_user, mock_session, uuid.uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_user_template_success(mock_session, mock_user, mock_user_template):
    exec_result = Mock()
    exec_result.first.return_value = mock_user_template
    mock_session.exec.return_value = exec_result

    await duplicate_user_template(mock_user, mock_session, mock_user_template.id)

    mock_session.add.assert_called()
    mock_session.commit.assert_awaited()

    duplicated_template = mock_session.add.call_args.args[0]
    duplicated_name_suffix = " (Copy)"
    assert duplicated_template.name == mock_user_template.name + duplicated_name_suffix
    assert duplicated_template.content == mock_user_template.content
    assert duplicated_template.description == mock_user_template.description


@pytest.mark.asyncio
async def test_duplicate_user_template_not_found(mock_session, mock_user):
    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await duplicate_user_template(mock_user, mock_session, uuid.uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_edit_user_template_question_at_index_zero_is_updated(mock_session, mock_user, mock_user_template):
    existing_question = Mock()
    existing_question.id = uuid.uuid4()
    existing_question.position = 0
    existing_question.title = "Old Title"
    existing_question.description = "Old Description"

    exec_result = Mock()
    exec_result.first.return_value = mock_user_template

    exec_q = Mock()
    exec_q.all.return_value = [existing_question]

    mock_session.exec.side_effect = [exec_result, exec_q]

    request = SimpleNamespace(
        name=None,
        content=None,
        heading=None,
        description=None,
        questions=[Question(id=existing_question.id, position=0, title="New Title", description="New Description")],
    )

    await edit_user_template(mock_user, mock_session, mock_user_template.id, request)

    mock_session.add.assert_not_called()
    assert existing_question.title == "New Title"


@pytest.mark.asyncio
async def test_edit_user_template_adds_new_question_when_no_id(
    mock_session, mock_user, mock_user_template, mock_request
):
    mock_request.questions = [
        SimpleNamespace(id=None, position=1, title="Foo", description="foobar", format_instructions="")
    ]

    exec_result = Mock()
    exec_result.first.return_value = mock_user_template

    exec_q = Mock()
    exec_q.all.return_value = []

    mock_session.exec.side_effect = [exec_result, exec_q]

    await edit_user_template(mock_user, mock_session, mock_user_template.id, mock_request)

    mock_session.add.assert_called_once()

    added = mock_session.add.call_args.args[0]
    assert added.title == mock_request.questions[0].title
    assert added.position == mock_request.questions[0].position
    assert added.user_template_id == mock_user_template.id
