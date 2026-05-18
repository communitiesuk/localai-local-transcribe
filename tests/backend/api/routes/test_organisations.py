import pytest
from uuid import uuid4
from httpx import AsyncClient
from fastapi import FastAPI


from backend.api.routes.organisations import (
    organisations_router, 
    list_organisations, 
    create_organisation, 
    delete_organisation, 
    update_organisations_domains
)

from tests.utils import get_test_client
from contextlib import asynccontextmanager
import pytest_asyncio



# -------------------------------------------------
# FAKES
# -------------------------------------------------

class FakeUser:
    def __init__(self, is_admin=True):
        self.is_admin = is_admin


class FakeOrg:
    def __init__(self, id, name, allowed_domains=None):
        self.id = id
        self.name = name
        self.allowed_domains = allowed_domains or []


class FakeSession:
    """
    In-memory session replacement.
    """

    def __init__(self):
        self.store = {}

    async def exec(self, query=None):
        class Result:
            def __init__(self, items):
                self._items = items

            def first(self):
                return self._items[0] if self._items else None

            def all(self):
                return self._items

        return Result(list(self.store.values()))

    async def get(self, model, id):
        return self.store.get(id)

    def add(self, obj):
        self.store[obj.id] = obj

    async def commit(self):
        pass

    async def refresh(self, obj):
        return obj

    async def delete(self, obj):
        self.store.pop(obj.id, None)


@pytest_asyncio.fixture
async def async_test_client():
    async with get_test_client() as ac:
        yield ac

# -------------------------------------------------
# FIXTURES
# -------------------------------------------------

@pytest.fixture
def fake_session():
    return FakeSession()

@pytest.fixture(autouse=True)
def override_dependencies(fake_session):
    """
    Applied to all tests.
    """

    app.dependency_overrides[get_current_user] = lambda: FakeUser(is_admin=True)
    app.dependency_overrides[get_session] = lambda: fake_session

    yield

    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    async with get_test_client() as ac:
        yield ac


# -------------------------------------------------
# TESTS
# -------------------------------------------------

@pytest.mark.asyncio
async def test_list_organisations_empty(client):
    response = await client.get("/organisations")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_organisation(client):
    response = await client.post(
        "/organisations",
        json={
            "name": "Test Org",
            "allowed_domains": ["test.com"],
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Test Org"
    assert data["allowed_domains"] == ["test.com"]


@pytest.mark.asyncio
async def test_create_duplicate_organisation(client):
    # First create
    await client.post(
        "/organisations",
        json={
            "name": "Duplicate Org",
            "allowed_domains": [],
        },
    )

    # Second attempt
    response = await client.post(
        "/organisations",
        json={
            "name": "Duplicate Org",
            "allowed_domains": [],
        },
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_patch_organisation(client):
    org_id = str(uuid4())

    session = FakeSession()
    session.store[org_id] = FakeOrg(
        id=org_id,
        name="Patch Org",
        allowed_domains=[],
    )

    app.dependency_overrides[get_session] = lambda: session

    response = await client.patch(
        f"/organisations/{org_id}",
        json={"allowed_domains": ["new.com"]},
    )

    assert response.status_code == 200
    assert response.json()["allowed_domains"] == ["new.com"]


@pytest.mark.asyncio
async def test_delete_organisation(client):
    org_id = str(uuid4())

    session = FakeSession()
    session.store[org_id] = FakeOrg(
        id=org_id,
        name="Delete Org",
    )

    app.dependency_overrides[get_session] = lambda: session

    response = await client.delete(f"/organisations/{org_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_requires_admin(client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(is_admin=False)

    response = await client.get("/organisations")

    assert response.status_code == 403