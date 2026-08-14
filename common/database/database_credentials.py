from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

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
    target_engine = engine if isinstance(engine, Engine) else engine.sync_engine

    @event.listens_for(target_engine, "do_connect")
    def _do_connect(dialect: Dialect, _: object, cargs: tuple[Any, ...], cparams: dict[str, Any]) -> Any:
        credentials = credential_provider.get_credentials()
        cparams["user"] = credentials.username
        cparams["password"] = credentials.password

        return dialect.connect(*cargs, **cparams)
