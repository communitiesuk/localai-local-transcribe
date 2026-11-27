"""Minimal POC for reading AppConfig feature flags from the backend.

In deployed environments, reads via the appconfig-agent ECS sidecar, which polls AppConfig and
serves the latest configuration locally - matching the AWS.AppConfig.FeatureFlags JSON shape
(see terraform/modules/app_config/feature_flags.json).

Locally, reads the feature_flags.json file straight off disk instead - no sidecar, AWS
credentials, or APP_CONFIG_* settings are needed. This reflects the local working copy of the
file rather than whatever is actually deployed.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from common.settings import get_settings

APPCONFIG_AGENT_PORT = 2772

# backend/api/feature_flags/client.py -> backend/ -> repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_FEATURE_FLAGS_FILE = REPO_ROOT / "terraform" / "modules" / "app_config" / "feature_flags.json"


class FeatureFlagsNotConfiguredError(Exception):
    """Raised when AppConfig isn't configured for this environment (e.g. APP_CONFIG_* unset)."""


async def get_feature_flags_config() -> Any:
    """Return the full AppConfig configuration document."""
    settings = get_settings()

    if settings.ENVIRONMENT.lower() == "local":
        return await asyncio.to_thread(_get_config_from_file)

    if (
        not settings.APP_CONFIG_APPLICATION_ID
        or not settings.APP_CONFIG_ENVIRONMENT_ID
        or not settings.APP_CONFIG_CONFIGURATION_PROFILE_ID
    ):
        msg = "AppConfig is not configured for this environment (APP_CONFIG_* settings are unset)"
        raise FeatureFlagsNotConfiguredError(msg)

    return await _get_config_via_agent(
        settings.APP_CONFIG_APPLICATION_ID,
        settings.APP_CONFIG_ENVIRONMENT_ID,
        settings.APP_CONFIG_CONFIGURATION_PROFILE_ID,
    )


async def get_feature_flag_enabled(flag_name: str) -> bool:
    """Return whether `flag_name` is enabled."""
    config = await get_feature_flags_config()
    return bool(config.get("values", {}).get(flag_name, {}).get("enabled", False))


async def _get_config_via_agent(application_id: str, environment_id: str, configuration_profile_id: str) -> Any:
    url = (
        f"http://localhost:{APPCONFIG_AGENT_PORT}/applications/{application_id}"
        f"/environments/{environment_id}/configurations/{configuration_profile_id}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def _get_config_from_file() -> Any:
    return json.loads(DEFAULT_FEATURE_FLAGS_FILE.read_text())
