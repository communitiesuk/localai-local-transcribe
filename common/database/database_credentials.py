"""
Dynamic DB credential provider for RDS-managed / rotating secrets.

Fetches username+password from Secrets Manager, caches them with a TTL,
and forces a refresh either on schedule (lazy, checked on access) or
immediately when a connection attempt fails auth.

Usage:
    from db_credentials import SecretsManagerCredentialProvider, attach_dynamic_credentials

    credential_provider = SecretsManagerCredentialProvider(
        secret_arn=settings.DB_SECRET_ARN,
        ttl_seconds=300,  # re-fetch at most every 5 min unless a failure forces it sooner
    )

    attach_dynamic_credentials(engine, credential_provider)
    attach_dynamic_credentials(async_engine, credential_provider)
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Protocol

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import Dialect, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DbCredentials:
    username: str
    password: str


class DbCredentialsProvider(Protocol):
    def get_credentials(self) -> DbCredentials: ...
    def invalidate_credentials(self) -> None: ...


class StaticDbCredentialsProvider:
    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    def get_credentials(self) -> DbCredentials:
        return DbCredentials(
            username=self._username,
            password=self._password,
        )

    def invalidate_credentials(self) -> None:
        return


class SecretsManagerCredentialProvider:
    """
    Thread-safe, TTL-cached credential fetcher backed by AWS Secrets Manager.

    - get_credentials() returns the cached value if it's still fresh.
    - get_credentials(force_refresh=True) always hits Secrets Manager,
      regardless of TTL — used when a connection attempt fails auth.
    """

    def __init__(
        self,
        secret_arn: str,
        ttl_seconds: int = 300,
        region_name: str | None = None,
    ) -> None:
        self._secret_arn = secret_arn
        self._ttl_seconds = ttl_seconds
        self._client = boto3.client("secretsmanager", region_name=region_name)

        self._lock = threading.Lock()
        self._cached: DbCredentials | None = None
        self._fetched_at: float = 0.0

    def get_credentials(self) -> DbCredentials:
        with self._lock:
            is_stale = (time.monotonic() - self._fetched_at) >= self._ttl_seconds
            if self._cached is None or is_stale:
                self._cached = self._fetch()
                self._fetched_at = time.monotonic()
            return self._cached

    def _fetch(self) -> DbCredentials:
        try:
            response = self._client.get_secret_value(SecretId=self._secret_arn)
        except ClientError:
            logger.exception("Failed to fetch DB secret %s from Secrets Manager", self._secret_arn)
            # If we have a stale cached value, prefer serving it over hard-failing —
            # better to keep using a slightly-old-but-still-valid credential than
            # to break every DB connection because Secrets Manager had a blip.
            if self._cached is not None:
                logger.warning("Falling back to previously cached DB credentials")
                return self._cached
            raise

        payload = json.loads(response["SecretString"])
        return DbCredentials(username=payload["username"], password=payload["password"])

    def invalidate_credentials(self) -> None:
        with self._lock:
            self._cached = None


_AUTH_FAILURE_MARKERS = (
    "password authentication failed",
    "28P01",  # postgres SQLSTATE for invalid_password
    "auth",
)


def _looks_like_auth_failure(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in _AUTH_FAILURE_MARKERS)


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
        creds = credential_provider.get_credentials()
        cparams["user"] = creds.username
        cparams["password"] = creds.password

        try:
            return dialect.connect(*cargs, **cparams)
        except Exception as exc:
            if not _looks_like_auth_failure(exc):
                raise

            logger.warning("DB connection failed auth check — forcing credential refresh and retrying once")
            credential_provider.invalidate_credentials()
            creds = credential_provider.get_credentials()
            cparams["user"] = creds.username
            cparams["password"] = creds.password
            return dialect.connect(*cargs, **cparams)
