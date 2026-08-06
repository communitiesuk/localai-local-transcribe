import logging
import ssl

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Session, create_engine

from common.database.database_credentials import (
    DbCredentialsProvider,
    IamDbCredentialsProvider,
    StaticDbCredentialsProvider,
    attach_dynamic_credentials,
)
from common.settings import get_settings

logger = logging.getLogger(__name__)

# Only create the settings object once

settings = get_settings()


DB_USER = settings.POSTGRES_USER
DB_PASSWORD = settings.POSTGRES_PASSWORD  # Only used for local dev

DB_HOST = settings.POSTGRES_HOST
DB_PORT = settings.POSTGRES_PORT
DB_NAME = settings.POSTGRES_DB

# URL deliberately omits user/password — do_connect fills them in per attempt.
SYNC_DATABASE_URL = f"postgresql+psycopg2://{DB_HOST}:{DB_PORT}/{DB_NAME}"
ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_HOST}:{DB_PORT}/{DB_NAME}"

sync_connect_args = {}
async_connect_args = {}
if settings.ENVIRONMENT in ["prod", "staging", "development"]:
    sync_connect_args = {
        "sslmode": "verify-full",
        "sslrootcert": settings.RDS_CA_BUNDLE_PATH,
    }
    async_connect_args = {
        "ssl": ssl.create_default_context(cafile=settings.RDS_CA_BUNDLE_PATH),
    }

engine = create_engine(
    SYNC_DATABASE_URL,
    connect_args=sync_connect_args,
    pool_size=20,
    max_overflow=30,
    pool_timeout=60,
    pool_pre_ping=True,
)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args=async_connect_args,
    pool_size=20,
    max_overflow=30,
    pool_timeout=60,
    pool_pre_ping=True,
    pool_recycle=1800,
)

credential_provider: DbCredentialsProvider
if settings.ENVIRONMENT == "local":
    if settings.POSTGRES_USER is None:
        msg = "POSTGRES_USER must be set"
        raise ValueError(msg)
    if settings.POSTGRES_PASSWORD is None:
        msg = "POSTGRES_PASSWORD must be set"
        raise ValueError(msg)
    credential_provider = StaticDbCredentialsProvider(
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )
else:
    if settings.POSTGRES_USER is None:
        msg = "POSTGRES_USER must be set"
        raise ValueError(msg)
    if settings.AWS_REGION is None:
        msg = "AWS_REGION must be set"
        raise ValueError(msg)
    credential_provider = IamDbCredentialsProvider(
        db_hostname=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        username=settings.POSTGRES_USER,
        region_name=settings.AWS_REGION,
    )

attach_dynamic_credentials(engine, credential_provider)
attach_dynamic_credentials(async_engine, credential_provider)


def SessionLocal() -> Session:  # noqa: N802
    return Session(engine)
