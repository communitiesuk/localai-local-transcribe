import asyncio
from typing import Any

import sentry_sdk

from common.settings import get_settings
from worker.worker_service import create_worker_service

settings = get_settings()


if settings.SENTRY_DSN:
    sentry_init_opts: dict[str, Any] = {
        "send_default_pii": settings.ENVIRONMENT != "prod",
        "traces_sample_rate": 1.0,
        "profile_session_sample_rate": 0.2 if settings.ENVIRONMENT == "prod" else 1.0,
    }
    sentry_sdk.init(settings.SENTRY_DSN, environment=settings.ENVIRONMENT, **sentry_init_opts)

if __name__ == "__main__":
    worker_service = create_worker_service()
    asyncio.run(worker_service.run())
