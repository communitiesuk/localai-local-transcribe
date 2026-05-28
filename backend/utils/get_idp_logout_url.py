import httpx
from functools import lru_cache
from common.settings import get_settings
import logging
from typing import Any

settings = get_settings()
logger = logging.getLogger(__name__)


async def get_idp_logout_url() -> str:
    """
    Fetches the logout endpoint from the IdP's OIDC discovery document.
    """

    issuer = settings.OIDC_ISSUER  
    discovery_url = f"{issuer}/.well-known/openid-configuration"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(discovery_url)
        response.raise_for_status()
        config: dict[str, Any] = response.json()

    
    logout_url = config.get("end_session_endpoint")
    
    if not isinstance(logout_url, str):
        raise ValueError("IdP does not expose an end_session_endpoint")
    
    return logout_url