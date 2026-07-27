import logging

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Session, create_engine

from common.settings import get_settings
from common.database.database_credentials import SecretsManagerCredentialProvider, attach_dynamic_credentials

logger = logging.getLogger(__name__)

# Only create the settings object once

settings = get_settings()


# Get database connection details from environment variables
DB_USER = settings.POSTGRES_USER
DB_PASSWORD = settings.POSTGRES_PASSWORD

# Host/port/db are stable and can stay as plain settings.
# User/password are NO LONGER read here — they're injected per-connection
# by the credential provider below, since they now rotate.
DB_HOST = settings.POSTGRES_HOST
DB_PORT = settings.POSTGRES_PORT
DB_NAME = settings.POSTGRES_DB
 
# URL deliberately omits user/password — do_connect fills them in per attempt.
SYNC_DATABASE_URL = f"postgresql+psycopg2://{DB_HOST}:{DB_PORT}/{DB_NAME}"
ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_HOST}:{DB_PORT}/{DB_NAME}"
 
engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=60,
    pool_pre_ping=True,
    pool_recycle=1800,  # recycle idle connections every 30 min so they periodically
                          # pick up freshly cached creds, independent of any failure
)
 
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=60,
    pool_pre_ping=True,
    pool_recycle=1800,
)
 
credential_provider = SecretsManagerCredentialProvider(
    secret_arn=settings.DB_SECRET_ARN,  # the backend_user secret ARN from Secrets Manager
    ttl_seconds=300,  # scheduled refresh: re-fetch at most every 5 minutes
)
 
attach_dynamic_credentials(engine, credential_provider)
attach_dynamic_credentials(async_engine, credential_provider)
 
# Optional: keep the cache proactively warm so connection attempts never pay
# the Secrets Manager round-trip. Not required for correctness.
credential_provider.start_background_refresh()
 
 
def SessionLocal() -> Session:  # noqa: N802
    return Session(engine)
