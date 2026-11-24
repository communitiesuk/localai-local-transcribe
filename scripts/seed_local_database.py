"""Seed a local database with the rows needed to sign in and use the site.

Local development skips real authentication and always presents the same user, defined in
``common.auth``. That user still has to exist in the database, because the app does not create
accounts on login, so a newly created database leaves you locked out until the rows are added by
hand. This adds them instead.

The script only ever inserts, it does nothing on a database that has already been seeded, and it
refuses to run unless everything it can check says the database is a local one.

    poetry run python -m scripts.seed_local_database
"""

from __future__ import annotations

import logging
import os
import sys

from sqlmodel import Session, col, select

from common.auth import LOCAL_USER_EMAIL, LOCAL_USER_SUBJECT_ID
from common.database.postgres_models import Organisation, User, UserRole
from common.settings import Settings, get_settings

logger = logging.getLogger(__name__)

LOCAL_ORGANISATION_NAME = "Test Council"
LOCAL_ORGANISATION_DOMAINS = ("test.co.uk",)
LOCAL_USER_NAME = "Test User"

# Every role, so that the admin only pages are reachable on a local setup.
LOCAL_USER_ROLES = (UserRole.STANDARD_USER, UserRole.LOCAL_AUTHORITY_ADMIN, UserRole.MHCLG_SUPPORT_ADMIN)

LOCAL_DATABASE_HOSTS = frozenset({"localhost", "127.0.0.1", "db"})


class SeedRefusedError(Exception):
    """The target is not plainly a local database, so nothing was written."""


def check_target_is_local(settings: Settings, environment: str | None) -> None:
    """Refuse anything that is not plainly a local database.

    ``environment`` comes from the process environment rather than from settings, because
    ``Settings.ENVIRONMENT`` defaults to "local" and an unset variable would otherwise pass.
    """
    if environment != "local":
        msg = f"ENVIRONMENT must be set to 'local', it is {environment!r}. Nothing was written."
        raise SeedRefusedError(msg)

    if settings.POSTGRES_HOST not in LOCAL_DATABASE_HOSTS:
        msg = (
            f"POSTGRES_HOST is {settings.POSTGRES_HOST!r}, which is not one of "
            f"{sorted(LOCAL_DATABASE_HOSTS)}. Nothing was written."
        )
        raise SeedRefusedError(msg)

    if settings.POSTGRES_HOSTADDR is not None:
        msg = (
            "POSTGRES_HOSTADDR is set, so the connection is tunnelled to a database somewhere else. "
            "Nothing was written."
        )
        raise SeedRefusedError(msg)


def check_database_holds_no_other_users(session: Session) -> None:
    """Refuse a database that holds users this script did not create.

    This is the only check that looks at what is in the database rather than at what the
    configuration claims, so it is the one that catches a local looking connection to a real
    database.
    """
    statement = select(User).where(col(User.email) != LOCAL_USER_EMAIL)
    if session.exec(statement).first() is not None:
        msg = (
            "This database holds users other than the local one, so it does not look like a local "
            "database. Nothing was written."
        )
        raise SeedRefusedError(msg)


def seed_organisation(session: Session) -> Organisation:
    statement = select(Organisation).where(col(Organisation.name) == LOCAL_ORGANISATION_NAME)
    existing = session.exec(statement).first()
    if existing is not None:
        logger.info("Organisation '%s' is already there", LOCAL_ORGANISATION_NAME)
        return existing

    organisation = Organisation(name=LOCAL_ORGANISATION_NAME, allowed_domains=list(LOCAL_ORGANISATION_DOMAINS))
    session.add(organisation)
    logger.info("Added organisation '%s'", LOCAL_ORGANISATION_NAME)
    return organisation


def seed_user(session: Session, organisation: Organisation) -> User:
    statement = select(User).where(col(User.subject_id) == LOCAL_USER_SUBJECT_ID)
    existing = session.exec(statement).first()
    if existing is not None:
        logger.info("The local user is already there")
        return existing

    user = User(
        subject_id=LOCAL_USER_SUBJECT_ID,
        email=LOCAL_USER_EMAIL,
        name=LOCAL_USER_NAME,
        roles=list(LOCAL_USER_ROLES),
        organisation_id=organisation.id,
    )
    session.add(user)
    logger.info("Added the local user with roles %s", [role.value for role in LOCAL_USER_ROLES])
    return user


def seed(session: Session) -> None:
    check_database_holds_no_other_users(session)
    organisation = seed_organisation(session)
    seed_user(session, organisation)
    session.commit()


def main() -> None:
    settings = get_settings()
    check_target_is_local(settings, os.environ.get("ENVIRONMENT"))

    # Imported here so the checks above run before a connection pool is built.
    from common.database.postgres_database import SessionLocal

    with SessionLocal() as session:
        seed(session)

    logger.info("Local database seeded, sign in at %s", settings.APP_URL)


if __name__ == "__main__":
    try:
        main()
    except SeedRefusedError as error:
        sys.exit(str(error))
