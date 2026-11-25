"""Minimal POC for reading AppConfig feature flags from the backend.

In deployed environments, reads via the appconfig-agent ECS sidecar, which polls AppConfig and
serves the latest configuration locally - matching the AWS.AppConfig.FeatureFlags JSON shape
(see terraform/modules/app_config/feature_flags.json).

Locally (no sidecar), falls back to calling AppConfig directly via boto3, using the same
list_deployments + get_hosted_configuration_version approach as
scripts/deploy_feature_flags/app_config/client.py, picking up credentials from the normal boto3
chain. Requires APP_CONFIG_* to be set manually (e.g. via .env) since docker-compose doesn't
provision them.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import boto3
import httpx

from common.settings import get_settings

APPCONFIG_AGENT_PORT = 2772

# Deployments in these states aren't actively serving their ConfigurationVersion - see
# scripts/deploy_feature_flags/app_config/client.py for the same convention.
INACTIVE_DEPLOYMENT_STATES = {"ROLLED_BACK", "REVERTED"}


class FeatureFlagsNotConfiguredError(Exception):
    """Raised when AppConfig isn't configured for this environment (e.g. APP_CONFIG_* unset)."""


async def get_feature_flags_config() -> Any:
    """Return the full AppConfig configuration document, read live from AppConfig."""
    settings = get_settings()
    if (
        not settings.APP_CONFIG_APPLICATION_ID
        or not settings.APP_CONFIG_ENVIRONMENT_ID
        or not settings.APP_CONFIG_CONFIGURATION_PROFILE_ID
    ):
        msg = "AppConfig is not configured for this environment (APP_CONFIG_* settings are unset)"
        raise FeatureFlagsNotConfiguredError(msg)

    if settings.ENVIRONMENT.lower() == "local":
        return await asyncio.to_thread(
            _get_config_via_boto3,
            settings.APP_CONFIG_APPLICATION_ID,
            settings.APP_CONFIG_ENVIRONMENT_ID,
            settings.APP_CONFIG_CONFIGURATION_PROFILE_ID,
        )

    return await _get_config_via_agent(
        settings.APP_CONFIG_APPLICATION_ID,
        settings.APP_CONFIG_ENVIRONMENT_ID,
        settings.APP_CONFIG_CONFIGURATION_PROFILE_ID,
    )


async def get_feature_flag_enabled(flag_name: str) -> bool:
    """Return whether `flag_name` is enabled, read live from AppConfig."""
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


def _get_config_via_boto3(application_id: str, environment_id: str, configuration_profile_id: str) -> Any:
    client = boto3.client("appconfig")

    version_number = None
    paginator = client.get_paginator("list_deployments")
    for page in paginator.paginate(ApplicationId=application_id, EnvironmentId=environment_id):
        # list_deployments returns items ordered most-recent-first.
        for deployment in page.get("Items", []):
            if deployment["State"] in INACTIVE_DEPLOYMENT_STATES:
                continue
            version_number = int(deployment["ConfigurationVersion"])
            break
        if version_number is not None:
            break

    if version_number is None:
        msg = "No deployed AppConfig configuration found for this environment"
        raise FeatureFlagsNotConfiguredError(msg)

    response = client.get_hosted_configuration_version(
        ApplicationId=application_id,
        ConfigurationProfileId=configuration_profile_id,
        VersionNumber=version_number,
    )
    content_bytes = response["Content"].read()
    return json.loads(content_bytes)
