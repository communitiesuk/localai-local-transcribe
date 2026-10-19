from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from common.database.database_credentials import IamDbCredentialsProvider, StaticDbCredentialsProvider
from common.settings import Settings
from reporting.aggregate_analytics import database
from reporting.aggregate_analytics.database import (
    EventRow,
    build_engine,
    count_rows,
    credential_provider,
    fetch_event_rows,
    monthly_count_rows,
)

ORG_A = "11111111-1111-1111-1111-111111111111"

ROWS = [
    EventRow("SUMMARY_RECEIVED", None, ORG_A, "2026-09", 10),
    EventRow("TRANSCRIPTION_RECEIVED", "live_recording", ORG_A, "2026-09", 7),
    EventRow("TRANSCRIPTION_RECEIVED", "direct_upload", None, "2026-10", 3),
]


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "POSTGRES_HOST": "db.example.rds.amazonaws.com",
        "POSTGRES_PORT": 5433,
        "POSTGRES_DB": "postgres",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": None,
        "POSTGRES_HOSTADDR": None,
        "POSTGRES_IAM_PORT": None,
        "RDS_CA_BUNDLE_PATH": "/tmp/bundle.pem",  # noqa: S108
        "ENVIRONMENT": "production",
        "AWS_REGION": "eu-west-2",
    }
    return Settings.model_construct(**{**values, **overrides})


def test_count_rows_filters_by_event_and_recording_source() -> None:
    assert count_rows(ROWS, "TRANSCRIPTION_RECEIVED") == 10
    assert count_rows(ROWS, "TRANSCRIPTION_RECEIVED", "live_recording") == 7
    assert count_rows(ROWS, "SUMMARY_RECEIVED") == 10


def test_monthly_count_rows_groups_by_month_and_optionally_organisation() -> None:
    assert monthly_count_rows(ROWS, ("TRANSCRIPTION_RECEIVED",), by_organisation=False) == {
        (None, "2026-09"): 7,
        (None, "2026-10"): 3,
    }
    assert monthly_count_rows(ROWS, ("TRANSCRIPTION_RECEIVED",), by_organisation=True) == {
        (ORG_A, "2026-09"): 7,
        (None, "2026-10"): 3,
    }


def test_local_environment_uses_static_credentials() -> None:
    provider = credential_provider(make_settings(ENVIRONMENT="local", POSTGRES_PASSWORD="insecure"))

    assert isinstance(provider, StaticDbCredentialsProvider)


def test_local_environment_requires_a_password() -> None:
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD"):
        credential_provider(make_settings(ENVIRONMENT="local"))


def test_other_environments_use_iam_with_the_iam_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("common.database.database_credentials.boto3.client", MagicMock())

    provider = credential_provider(make_settings(POSTGRES_IAM_PORT=5432))

    assert isinstance(provider, IamDbCredentialsProvider)
    assert provider.db_hostname == "db.example.rds.amazonaws.com"
    assert provider.port == 5432


def test_iam_port_defaults_to_the_connection_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("common.database.database_credentials.boto3.client", MagicMock())

    provider = credential_provider(make_settings())

    assert isinstance(provider, IamDbCredentialsProvider)
    assert provider.port == 5433


def test_iam_requires_user_and_region() -> None:
    with pytest.raises(ValueError, match="POSTGRES_USER"):
        credential_provider(make_settings(POSTGRES_USER=None))
    with pytest.raises(ValueError, match="AWS_REGION"):
        credential_provider(make_settings(AWS_REGION=None))


def test_tunnel_engine_connects_to_hostaddr_with_verified_tls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("common.database.database_credentials.boto3.client", MagicMock())
    create = MagicMock()
    monkeypatch.setattr(database, "create_engine", create)
    monkeypatch.setattr(database, "attach_dynamic_credentials", MagicMock())

    build_engine(make_settings(POSTGRES_HOSTADDR="127.0.0.1"))

    assert create.call_args.args[0] == "postgresql+psycopg2://db.example.rds.amazonaws.com:5433/postgres"
    assert create.call_args.kwargs["connect_args"] == {
        "hostaddr": "127.0.0.1",
        "sslmode": "verify-full",
        "sslrootcert": "/tmp/bundle.pem",  # noqa: S108
    }


def test_local_engine_has_no_tls_or_hostaddr(monkeypatch: pytest.MonkeyPatch) -> None:
    create = MagicMock()
    monkeypatch.setattr(database, "create_engine", create)
    monkeypatch.setattr(database, "attach_dynamic_credentials", MagicMock())

    build_engine(make_settings(ENVIRONMENT="local", POSTGRES_PASSWORD="insecure"))

    assert create.call_args.kwargs["connect_args"] == {}


def test_fetch_event_rows_maps_rows_and_passes_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import date

    db_rows = [
        SimpleNamespace(
            event_type="SUMMARY_RECEIVED",
            recording_source="",
            organisation_id=ORG_A.upper(),
            month="2026-09",
            event_count=10,
        ),
        SimpleNamespace(
            event_type="TRANSCRIPTION_RECEIVED",
            recording_source="live_recording",
            organisation_id="",
            month="2026-10",
            event_count=3,
        ),
    ]
    session = MagicMock()
    session.__enter__.return_value = session
    session.execute.return_value = db_rows
    engine = MagicMock()
    monkeypatch.setattr(database, "get_settings", MagicMock())
    monkeypatch.setattr(database, "build_engine", MagicMock(return_value=engine))
    monkeypatch.setattr(database, "Session", MagicMock(return_value=session))

    rows = fetch_event_rows(date(2026, 9, 1), date(2026, 10, 31))

    assert rows == [
        EventRow("SUMMARY_RECEIVED", None, ORG_A, "2026-09", 10),
        EventRow("TRANSCRIPTION_RECEIVED", "live_recording", None, "2026-10", 3),
    ]
    assert session.execute.call_args.args[1] == {"start": date(2026, 9, 1), "end": date(2026, 10, 31)}
    engine.dispose.assert_called_once()
