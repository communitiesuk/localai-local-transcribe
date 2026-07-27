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

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DbCredentials:
    username: str
    password: str


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

    def get_credentials(self, force_refresh: bool = False) -> DbCredentials:
        with self._lock:
            is_stale = (time.monotonic() - self._fetched_at) >= self._ttl_seconds
            if self._cached is None or force_refresh or is_stale:
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

    def start_background_refresh(self, interval_seconds: int | None = None) -> None:
        """
        Optional: proactively refresh the cache on a schedule in a background
        thread, so the cache is always warm and connection attempts never pay
        the Secrets Manager round-trip latency. Not required for correctness —
        get_credentials() already refreshes lazily on TTL expiry — but keeps
        connect-time latency flat.
        """
        interval = interval_seconds or self._ttl_seconds

        def _loop() -> None:
            while True:
                time.sleep(interval)
                try:
                    self.get_credentials(force_refresh=True)
                    logger.info("Background DB credential refresh succeeded")
                except Exception:
                    logger.exception("Background DB credential refresh failed")

        thread = threading.Thread(target=_loop, daemon=True, name="db-credential-refresh")
        thread.start()


_AUTH_FAILURE_MARKERS = (
    "password authentication failed",
    "28P01",  # postgres SQLSTATE for invalid_password
    "auth",
)


def _looks_like_auth_failure(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in _AUTH_FAILURE_MARKERS)


def attach_dynamic_credentials(engine: Engine, credential_provider: SecretsManagerCredentialProvider) -> None:
    """
    Registers a do_connect listener that:
      1. Injects the current cached credentials into every new physical connection.
      2. If the connection attempt fails with what looks like an auth error,
         forces a credential refresh and retries once before giving up.

    The engine's connection URL should NOT embed a real user/password —
    build it with host/port/db only; this listener supplies credentials
    for every connection attempt.
    """

    @event.listens_for(engine, "do_connect")
    def _do_connect(dialect, conn_rec, cargs, cparams):  # noqa: ANN001
        creds = credential_provider.get_credentials()
        cparams["user"] = creds.username
        cparams["password"] = creds.password

        try:
            return dialect.connect(*cargs, **cparams)
        except Exception as exc:  # noqa: BLE001 - intentionally broad, filtered below
            if not _looks_like_auth_failure(exc):
                raise

            logger.warning("DB connection failed auth check — forcing credential refresh and retrying once")
            creds = credential_provider.get_credentials(force_refresh=True)
            cparams["user"] = creds.username
            cparams["password"] = creds.password
            return dialect.connect(*cargs, **cparams)