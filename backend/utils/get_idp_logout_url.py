import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

import httpx

from common.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

CACHE_TTL: Final = timedelta(hours=1)


@dataclass
class LogoutUrlCache:
    url: str | None = None
    cached_at: datetime | None = None


_logout_cache = LogoutUrlCache()


async def get_idp_logout_url() -> str | None:
    """
    Fetch the IdP logout URL from the OIDC discovery document,
    caching it for a short period.
    """
    now = datetime.now(UTC)

    if _logout_cache.url and _logout_cache.cached_at and now - _logout_cache.cached_at < CACHE_TTL:
        return _logout_cache.url

    try:
        issuer = settings.OIDC_ISSUER
        discovery_url = f"{issuer}/.well-known/openid-configuration"

        async with httpx.AsyncClient() as client:
            response = await client.get(discovery_url)
            response.raise_for_status()

        config: dict[str, Any] = response.json()

        logout_url = config.get("end_session_endpoint")

        if isinstance(logout_url, str):
            _logout_cache.url = logout_url
            _logout_cache.cached_at = now
            return logout_url

    except Exception:
        logger.exception("Failed to fetch IdP logout URL from discovery document")

    return None
