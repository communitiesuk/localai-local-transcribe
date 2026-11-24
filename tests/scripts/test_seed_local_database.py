from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from common.auth import LOCAL_USER_EMAIL, LOCAL_USER_SUBJECT_ID
from common.database.postgres_models import Organisation, User, UserRole
from scripts.seed_local_database import (
    LOCAL_ORGANISATION_NAME,
    SeedRefusedError,
    check_target_is_local,
    seed,
)


class FakeSession:
    """Hands back one queued result per query, in the order the script runs them."""

    def __init__(self, *results):
        self._results = list(results)
        self.added = []
        self.commits = 0

    def exec(self, _statement):
        return SimpleNamespace(first=self._results.pop(0))

    def add(self, instance):
        self.added.append(instance)

    def commit(self):
        self.commits += 1


def _session(*, other_user=None, organisation=None, user=None) -> FakeSession:
    return FakeSession(lambda: other_user, lambda: organisation, lambda: user)


def _local_settings() -> MagicMock:
    settings = MagicMock()
    settings.POSTGRES_HOST = "localhost"
    settings.POSTGRES_HOSTADDR = None
    return settings


class TestCheckTargetIsLocal:
    def test_allows_a_local_database(self):
        check_target_is_local(_local_settings(), "local")

    def test_refuses_when_the_environment_is_not_set(self):
        # Settings.ENVIRONMENT defaults to local, so an unset variable must not be read as one.
        with pytest.raises(SeedRefusedError):
            check_target_is_local(_local_settings(), None)

    def test_refuses_a_deployed_environment(self):
        with pytest.raises(SeedRefusedError):
            check_target_is_local(_local_settings(), "development")

    def test_refuses_a_host_that_is_not_local(self):
        settings = _local_settings()
        settings.POSTGRES_HOST = "development-database.eu-west-2.rds.amazonaws.com"

        with pytest.raises(SeedRefusedError):
            check_target_is_local(settings, "local")

    def test_refuses_a_connection_tunnelled_somewhere_else(self):
        settings = _local_settings()
        settings.POSTGRES_HOSTADDR = "127.0.0.1"

        with pytest.raises(SeedRefusedError):
            check_target_is_local(settings, "local")


class TestSeed:
    def test_adds_an_organisation_and_a_user_to_an_empty_database(self):
        session = _session()

        seed(session)

        organisation, user = session.added
        assert isinstance(organisation, Organisation)
        assert organisation.name == LOCAL_ORGANISATION_NAME
        assert isinstance(user, User)
        assert user.subject_id == LOCAL_USER_SUBJECT_ID
        assert user.email == LOCAL_USER_EMAIL
        assert session.commits == 1

    def test_puts_the_user_in_the_organisation_it_adds(self):
        session = _session()

        seed(session)

        organisation, user = session.added
        assert user.organisation_id == organisation.id

    def test_gives_the_local_user_every_role(self):
        session = _session()

        seed(session)

        _, user = session.added
        assert set(user.roles) == set(UserRole)

    def test_adds_nothing_when_the_database_is_already_seeded(self):
        organisation = Organisation(name=LOCAL_ORGANISATION_NAME)
        user = User(subject_id=LOCAL_USER_SUBJECT_ID, email=LOCAL_USER_EMAIL, organisation_id=organisation.id)
        session = _session(organisation=organisation, user=user)

        seed(session)

        assert session.added == []

    def test_refuses_and_writes_nothing_when_the_database_holds_other_users(self):
        session = _session(other_user=User(email="someone@example.gov.uk"))

        with pytest.raises(SeedRefusedError):
            seed(session)

        assert session.added == []
        assert session.commits == 0
