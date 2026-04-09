import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from backend.api.routes.templates import (
    create_user_template,
    delete_user_template,
    duplicate_user_template,
    edit_user_template,
    get_templates,
    get_user_template,
    get_user_templates,
)
from common.database.postgres_models import TemplateType
from common.services.template_manager import TemplateManager
from tests.utils import get_test_client


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("expected_status_code", [200])
async def test_get_templates_success(expected_status_code):
    async with get_test_client() as ac:
        response = await ac.get("/templates")
        assert response.status_code == expected_status_code
        assert len(response.json()) == len(TemplateManager.templates)


@pytest.mark.asyncio
async def test_get_templates_returns_list(make_user):
    res = get_templates(make_user)
    assert isinstance(res, list)


@pytest.mark.asyncio
async def test_get_user_templates_success(mock_session, make_user):
    tpl = Mock()
    tpl.id = uuid.uuid4()
    tpl.updated_datetime = datetime.now(tz=UTC)
    tpl.name = "Test Template"
    tpl.content = "Hello World"
    tpl.description = "test template"
    tpl.type = TemplateType.DOCUMENT

    exec_result = Mock()
    exec_result.all.return_value = [tpl]
    mock_session.exec.return_value = exec_result

    res = await get_user_templates(make_user, mock_session)
    assert len(res) == 1
    assert res[0].id == tpl.id
    assert res[0].name == "Test Template"


@pytest.mark.asyncio
async def test_get_user_template_success_and_not_found(mock_session, make_user):
    tpl = Mock()
    tpl.id = uuid.uuid4()
    tpl.updated_datetime = datetime.now(tz=UTC)
    tpl.name = "Test Template"
    tpl.content = "Hello World"
    tpl.description = "test template"
    tpl.type = TemplateType.DOCUMENT
    tpl.questions = []

    exec_result = Mock()
    exec_result.first.return_value = tpl
    mock_session.exec.return_value = exec_result

    res = await get_user_template(make_user, mock_session, tpl.id)
    assert res.id == tpl.id

    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result
    with pytest.raises(HTTPException):
        await get_user_template(make_user, mock_session, tpl.id)


@pytest.mark.asyncio
async def test_create_user_template_calls_add_and_commit(mock_session, make_user):
    request = SimpleNamespace(
        name="Test Template",
        content="Hello World",
        description="test template",
        type=TemplateType.DOCUMENT,
        questions=[SimpleNamespace(position=1, title="Foo", description="foobar")],
    )
    await create_user_template(make_user, mock_session, request)
    mock_session.add.assert_called()
    mock_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_edit_user_template_updates_and_questions_branch(mock_session, make_user):
    tpl = Mock()
    tpl.id = uuid.uuid4()
    tpl.user_id = make_user.id
    tpl.updated_datetime = datetime.now(tz=UTC)
    exec_result = Mock()
    exec_result.first.return_value = tpl
    mock_session.exec.return_value = exec_result

    exec_q = Mock()
    exec_q.all.return_value = []
    mock_session.exec.side_effect = [exec_result, exec_q]

    request = SimpleNamespace(
        name="New Request",
        content=None,
        description=None,
        questions=[SimpleNamespace(position=1, title="Test Question", description="Hello World")],
    )
    await edit_user_template(make_user, mock_session, tpl.id, request)
    mock_session.add.assert_called()
    mock_session.commit.assert_awaited()

    exec_result.first.return_value = None
    mock_session.exec.side_effect = [exec_result]
    with pytest.raises(HTTPException):
        await edit_user_template(make_user, mock_session, tpl.id, request)


@pytest.mark.asyncio
async def test_delete_user_template_success_and_not_found(mock_session, make_user):
    tpl = Mock()
    tpl.id = uuid.uuid4()
    tpl.user_id = make_user.id
    exec_result = Mock()
    exec_result.first.return_value = tpl
    mock_session.exec.return_value = exec_result

    await delete_user_template(make_user, mock_session, tpl.id)
    mock_session.delete.assert_awaited()
    mock_session.commit.assert_awaited()

    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result
    with pytest.raises(HTTPException):
        await delete_user_template(make_user, mock_session, tpl.id)


@pytest.mark.asyncio
async def test_duplicate_user_template_success_and_not_found(mock_session, make_user):
    original = Mock()
    original.id = uuid.uuid4()
    original.user_id = make_user.id
    original.name = "Test Template"
    original.description = "Hello World"
    original.content = "test template"
    original.type = TemplateType.DOCUMENT

    original.questions = []

    exec_result = Mock()
    exec_result.first.return_value = original
    mock_session.exec.return_value = exec_result

    await duplicate_user_template(make_user, mock_session, original.id)
    mock_session.add.assert_called()
    mock_session.commit.assert_awaited()

    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result
    with pytest.raises(HTTPException):
        await duplicate_user_template(make_user, mock_session, original.id)
