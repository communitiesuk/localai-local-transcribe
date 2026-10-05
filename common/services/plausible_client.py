import logging
from typing import Any

import httpx

from common.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

EVENT_PATH = "/api/event"
REQUEST_TIMEOUT_SECONDS = 5


class PlausibleClient:
    def __init__(self, domain: str, host: str) -> None:
        self.domain = domain
        self.url = f"{host.rstrip('/')}{EVENT_PATH}"

    def _payload(self, name: str, organisation_id: str | None) -> dict[str, Any]:
        payload: dict[str, Any] = {"domain": self.domain, "name": name, "url": f"https://{self.domain}/"}
        if organisation_id:
            payload["props"] = {"organisation_id": organisation_id}
        return payload

    async def send_event(
        self,
        name: str,
        organisation_id: str | None,
        user_agent: str,
        client_ip: str | None,
    ) -> None:
        """Send an event as the browser that triggered it.

        Plausible identifies a visitor from the user agent and IP, and drops events that carry a server or CDN
        address, so both are forwarded from the originating request rather than being ours.
        """
        headers = {"User-Agent": user_agent, "Content-Type": "application/json"}
        if client_ip:
            headers["X-Forwarded-For"] = client_ip

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(self.url, json=self._payload(name, organisation_id), headers=headers)
            response.raise_for_status()


plausible_client: PlausibleClient | None = None
if settings.PLAUSIBLE_DOMAIN:
    plausible_client = PlausibleClient(settings.PLAUSIBLE_DOMAIN, settings.PLAUSIBLE_HOST)
