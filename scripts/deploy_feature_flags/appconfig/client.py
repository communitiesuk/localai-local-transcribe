"""Helpers for the AWS AppConfig `appconfig` boto3 client."""

from __future__ import annotations

import json
from typing import Any

# Deployments in these states are not actively serving their ConfigurationVersion, so when
# looking for "the currently deployed version" they should be skipped in favour of an earlier one.
INACTIVE_DEPLOYMENT_STATES = {"ROLLED_BACK", "REVERTED"}


def get_deployed_version(client: Any, application_id: str, environment_id: str) -> int | None:
    """Return the configuration version number currently being served, or None if nothing's deployed yet."""
    paginator = client.get_paginator("list_deployments")
    for page in paginator.paginate(ApplicationId=application_id, EnvironmentId=environment_id):
        # list_deployments returns items ordered most-recent-first.
        for deployment in page.get("Items", []):
            if deployment["State"] in INACTIVE_DEPLOYMENT_STATES:
                continue
            return int(deployment["ConfigurationVersion"])
    return None


def get_deployed_content(
    client: Any, application_id: str, configuration_profile_id: str, version_number: int
) -> dict[str, Any]:
    response = client.get_hosted_configuration_version(
        ApplicationId=application_id,
        ConfigurationProfileId=configuration_profile_id,
        VersionNumber=version_number,
    )
    content_bytes = response["Content"].read()
    parsed: dict[str, Any] = json.loads(content_bytes)
    return parsed


def create_new_version(client: Any, application_id: str, configuration_profile_id: str, content_bytes: bytes) -> int:
    response = client.create_hosted_configuration_version(
        ApplicationId=application_id,
        ConfigurationProfileId=configuration_profile_id,
        Content=content_bytes,
        ContentType="application/json",
    )
    return int(response["VersionNumber"])


def validate_new_version(client: Any, application_id: str, configuration_profile_id: str, version_number: int) -> None:
    """Validate a hosted configuration version against the configuration profile's validators.
    Raises `botocore.exceptions.ClientError` (e.g. BadRequestException) if validation fails.
    """
    client.validate_configuration(
        ApplicationId=application_id,
        ConfigurationProfileId=configuration_profile_id,
        ConfigurationVersion=str(version_number),
    )


def start_deployment(
    client: Any,
    application_id: str,
    environment_id: str,
    configuration_profile_id: str,
    deployment_strategy_id: str,
    configuration_version: int,
) -> str:
    response = client.start_deployment(
        ApplicationId=application_id,
        EnvironmentId=environment_id,
        ConfigurationProfileId=configuration_profile_id,
        DeploymentStrategyId=deployment_strategy_id,
        ConfigurationVersion=str(configuration_version),
    )
    return str(response["DeploymentNumber"])
