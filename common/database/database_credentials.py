from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import boto3
from sqlalchemy import Dialect, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from common.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class DbCredentials:
    username: str
    password: str


class DbCredentialsProvider(Protocol):
    def get_credentials(self) -> DbCredentials: ...


class StaticDbCredentialsProvider:
    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    def get_credentials(self) -> DbCredentials:
        return DbCredentials(
            username=self._username,
            password=self._password,
        )


class IamDbCredentialsProvider:
    def __init__(self, db_hostname: str, port: int, username: str, region_name: str) -> None:
        self.db_hostname = db_hostname
        self.port = port
        self.username = username
        self.region_name = region_name
        self.client = boto3.client("rds", region_name=self.region_name)

    def get_credentials(self) -> DbCredentials:
        token = self.client.generate_db_auth_token(
            DBHostname=self.db_hostname, Port=self.port, DBUsername=self.username, Region=self.region_name
        )
        return DbCredentials(
            username=self.username,
            password=token,
        )


def attach_dynamic_credentials(engine: Engine | AsyncEngine, credential_provider: DbCredentialsProvider) -> None:
    """
    Registers a do_connect listener that:
      1. Injects the current cached credentials into every new physical connection.
      2. If the connection attempt fails with what looks like an auth error,
         forces a credential refresh and retries once before giving up.

    The engine's connection URL should NOT embed a real user/password —
    build it with host/port/db only; this listener supplies credentials
    for every connection attempt.
    """

    target_engine = engine if isinstance(engine, Engine) else engine.sync_engine

    @event.listens_for(target_engine, "do_connect")
    def _do_connect(dialect: Dialect, _, cargs, cparams):
        credentials = credential_provider.get_credentials()
        cparams["user"] = credentials.username
        cparams["password"] = credentials.password

        return dialect.connect(*cargs, **cparams)
