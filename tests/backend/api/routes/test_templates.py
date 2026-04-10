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
async def test_get_templates_returns_list(mock_user):
    res = get_templates(mock_user)
    assert isinstance(res, list)


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
async def test_create_user_template_calls_add_and_commit(mock_session, mock_user, mock_user_template, monkeypatch):
    request = SimpleNamespace(
        name="Test Template",
        content="Hello World",
        description="test template",
        type=TemplateType.DOCUMENT,
        questions=[SimpleNamespace(position=1, title="Foo", description="foobar")],
    )
    monkeypatch.setattr("backend.api.routes.templates.UserTemplate", lambda **_: mock_user_template)

    await create_user_template(mock_user, mock_session, request)
    mock_session.add.assert_called_once_with(mock_user_template)
    mock_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_edit_user_template_success(mock_session, mock_user, mock_user_template):
    exec_result = Mock()
    exec_result.first.return_value = mock_user_template

    exec_q = Mock()
    exec_q.all.return_value = []

    mock_session.exec.side_effect = [exec_result, exec_q]

    request = SimpleNamespace(
        name="New Request",
        content=None,
        description=None,
        questions=[SimpleNamespace(position=1, title="Test Question", description="Hello World")],
    )

    await edit_user_template(mock_user, mock_session, mock_user_template.id, request)

    mock_session.add.assert_called()
    mock_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_edit_user_template_not_found(mock_session, mock_user, mock_user_template):
    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.side_effect = [exec_result]

    request = SimpleNamespace(
        name="New Request",
        content=None,
        description=None,
        questions=[SimpleNamespace(position=1, title="Test Question", description="Hello World")],
    )

    with pytest.raises(HTTPException) as exc_info:
        await edit_user_template(mock_user, mock_session, mock_user_template.id, request)
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


@pytest.mark.asyncio
async def test_duplicate_user_template_not_found(mock_session, mock_user):
    exec_result = Mock()
    exec_result.first.return_value = None
    mock_session.exec.return_value = exec_result

    with pytest.raises(HTTPException) as exc_info:
        await duplicate_user_template(mock_user, mock_session, uuid.uuid4())
    assert exc_info.value.status_code == 404
