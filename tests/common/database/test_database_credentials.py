import json
import threading
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from common.database.database_credentials import (
    DbCredentials,
    SecretsManagerCredentialProvider,
    StaticDbCredentialsProvider,
)


def _secret_response(username: str, password: str) -> dict:
    # Mirrors the shape produced by the RDS multi-user rotation secret (see
    # terraform/modules/secrets/secrets.tf) — the provider reads only
    # username/password and ignores the rest.
    return {
        "SecretString": json.dumps(
            {
                "username": username,
                "password": password,
                "engine": "postgres",
                "host": "db.example.com",
                "port": 5432,
                "dbname": "local_transcribe",
                "masterarn": "arn:master",
            }
        )
    }


def _client_error() -> ClientError:
    return ClientError({"Error": {"Code": "InternalServiceError"}}, "GetSecretValue")


@pytest.fixture
def provider(monkeypatch):
    # Stop the constructor from building a real boto3 client (which would need a
    # resolvable AWS region); hand it a mock instead.
    monkeypatch.setattr(
        "common.database.database_credentials.boto3.client",
        lambda _service_name, **_kwargs: MagicMock(),
    )
    credential_provider = SecretsManagerCredentialProvider(secret_arn="arn:secret", ttl_seconds=300)
    credential_provider._client.get_secret_value = MagicMock(return_value=_secret_response("user", "pass"))  # noqa: SLF001
    return credential_provider


def test_get_credentials_fetches_on_first_call(provider):
    creds = provider.get_credentials()

    assert creds == DbCredentials(username="user", password="pass")
    provider._client.get_secret_value.assert_called_once_with(SecretId="arn:secret")  # noqa: SLF001


def test_get_credentials_returns_cached_value_without_re_fetching(provider):
    provider.get_credentials()
    provider.get_credentials()

    provider._client.get_secret_value.assert_called_once()  # noqa: SLF001


def test_get_credentials_refetches_once_ttl_expires(provider, monkeypatch):
    now = 1000.0
    monkeypatch.setattr("common.database.database_credentials.time.monotonic", lambda: now)
    provider._client.get_secret_value = MagicMock(  # noqa: SLF001
        side_effect=[_secret_response("user-1", "pass-1"), _secret_response("user-2", "pass-2")]
    )

    first = provider.get_credentials()
    now += provider._ttl_seconds  # noqa: SLF001
    second = provider.get_credentials()

    assert first == DbCredentials(username="user-1", password="pass-1")
    assert second == DbCredentials(username="user-2", password="pass-2")
    assert provider._client.get_secret_value.call_count == 2  # noqa: SLF001


def test_invalidate_credentials_causes_refetch(provider):
    provider._client.get_secret_value = MagicMock(  # noqa: SLF001
        side_effect=[_secret_response("user-1", "pass-1"), _secret_response("user-2", "pass-2")]
    )

    first = provider.get_credentials()
    provider.invalidate_credentials()
    second = provider.get_credentials()

    assert first == DbCredentials(username="user-1", password="pass-1")
    assert second == DbCredentials(username="user-2", password="pass-2")
    assert provider._client.get_secret_value.call_count == 2  # noqa: SLF001


def test_fetch_raises_client_error_when_no_cached_credentials(provider):
    provider._client.get_secret_value = MagicMock(side_effect=_client_error())  # noqa: SLF001

    with pytest.raises(ClientError):
        provider.get_credentials()


def test_concurrent_get_credentials_calls_only_fetch_once(provider):
    barrier = threading.Barrier(5)

    def fetch():
        barrier.wait()
        provider.get_credentials()

    threads = [threading.Thread(target=fetch) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    provider._client.get_secret_value.assert_called_once()  # noqa: SLF001


def test_static_provider_returns_initial_credentials():
    credential_provider = StaticDbCredentialsProvider(username="user", password="pass")

    assert credential_provider.get_credentials() == DbCredentials(username="user", password="pass")


def test_static_provider_invalidate_is_a_no_op():
    credential_provider = StaticDbCredentialsProvider(username="user", password="pass")
    credential_provider.invalidate_credentials()

    assert credential_provider.get_credentials() == DbCredentials(username="user", password="pass")
