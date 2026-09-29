import logging
from typing import Any

import httpx

from common.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

EVENT_PATH = "/api/event"
USER_AGENT = "local-transcribe"
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

    @property
    def _headers(self) -> dict[str, str]:
        return {"User-Agent": USER_AGENT, "Content-Type": "application/json"}

    def send_event(self, name: str, organisation_id: str | None = None) -> None:
        response = httpx.post(
            self.url,
            json=self._payload(name, organisation_id),
            headers=self._headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

    async def send_event_async(self, name: str, organisation_id: str | None = None) -> None:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(self.url, json=self._payload(name, organisation_id), headers=self._headers)
            response.raise_for_status()


plausible_client: PlausibleClient | None = None
if settings.PLAUSIBLE_DOMAIN:
    plausible_client = PlausibleClient(settings.PLAUSIBLE_DOMAIN, settings.PLAUSIBLE_HOST)
