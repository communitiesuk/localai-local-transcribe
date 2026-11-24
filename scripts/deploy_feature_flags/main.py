#!/usr/bin/env python3
"""Deploy feature_flags.json to AWS AppConfig if its contents differ from what's currently deployed.

All arguments can also be supplied via the equivalent env vars:
APPCONFIG_APPLICATION_ID, APPCONFIG_ENVIRONMENT_ID, APPCONFIG_CONFIGURATION_PROFILE_ID,
APPCONFIG_DEPLOYMENT_STRATEGY_ID, APPCONFIG_FEATURE_FLAGS_FILE.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import boto3
import jsonschema
from botocore.exceptions import ClientError

from .appconfig.client import (
    create_new_version,
    get_deployed_content,
    get_deployed_version,
    start_deployment,
    validate_new_version,
)
from .helpers import strip_ignored_keys, write_github_output
from .schema import validate_feature_flags

logger = logging.getLogger(__name__)

# scripts/deploy_feature_flags/main.py -> scripts/ -> repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_FEATURE_FLAGS_FILE = REPO_ROOT / "terraform" / "modules" / "app_config" / "feature_flags.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--application-id",
        default=os.environ.get("APPCONFIG_APPLICATION_ID"),
        required="APPCONFIG_APPLICATION_ID" not in os.environ,
    )
    parser.add_argument(
        "--environment-id",
        default=os.environ.get("APPCONFIG_ENVIRONMENT_ID"),
        required="APPCONFIG_ENVIRONMENT_ID" not in os.environ,
    )
    parser.add_argument(
        "--configuration-profile-id",
        default=os.environ.get("APPCONFIG_CONFIGURATION_PROFILE_ID"),
        required="APPCONFIG_CONFIGURATION_PROFILE_ID" not in os.environ,
    )
    parser.add_argument(
        "--deployment-strategy-id",
        default=os.environ.get("APPCONFIG_DEPLOYMENT_STRATEGY_ID"),
        required="APPCONFIG_DEPLOYMENT_STRATEGY_ID" not in os.environ,
    )
    parser.add_argument(
        "--feature-flags-file",
        default=os.environ.get("APPCONFIG_FEATURE_FLAGS_FILE", str(DEFAULT_FEATURE_FLAGS_FILE)),
        help=f"Path to the local feature flags JSON file (default: {DEFAULT_FEATURE_FLAGS_FILE})",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()

    feature_flags_path = Path(args.feature_flags_file)
    local_content = json.loads(feature_flags_path.read_text())
    local_content_bytes = feature_flags_path.read_bytes()

    try:
        validate_feature_flags(local_content)
    except jsonschema.exceptions.ValidationError as e:
        logger.error("%s does not conform to the AWS.AppConfig.FeatureFlags schema: %s", feature_flags_path, e.message)
        return 1

    client = boto3.client("appconfig")

    deployed_version = get_deployed_version(client, args.application_id, args.environment_id)

    if deployed_version is None:
        logger.info("No existing deployment found for this environment; treating as a change.")
        deployed_content: dict[str, Any] | None = None
    else:
        logger.info("Currently deployed configuration version: %s", deployed_version)
        deployed_content = get_deployed_content(
            client, args.application_id, args.configuration_profile_id, deployed_version
        )

    if deployed_content is not None and strip_ignored_keys(deployed_content) == strip_ignored_keys(local_content):
        logger.info("No changes detected between deployed configuration and %s. Exiting.", feature_flags_path)
        write_github_output("status", "no_change")
        return 0

    logger.info("Changes detected. Creating a new hosted configuration version from %s.", feature_flags_path)
    new_version = create_new_version(client, args.application_id, args.configuration_profile_id, local_content_bytes)
    logger.info("Created new hosted configuration version: %s", new_version)

    current_version = get_deployed_version(client, args.application_id, args.environment_id)
    if current_version != deployed_version:
        logger.error(
            "Aborting deployment: deployed configuration version changed from %s to %s "
            "since it was last read. A concurrent change may have occurred - re-run this script "
            "to reconcile against the latest state.",
            deployed_version,
            current_version,
        )
        return 1

    try:
        validate_new_version(client, args.application_id, args.configuration_profile_id, new_version)
    except ClientError:
        logger.exception("Configuration version %s failed validation.", new_version)
        return 1

    logger.info("Starting deployment of version %s.", new_version)
    try:
        deployment_number = start_deployment(
            client,
            args.application_id,
            args.environment_id,
            args.configuration_profile_id,
            args.deployment_strategy_id,
            new_version,
        )
    except ClientError:
        logger.exception("Failed to start feature flag deployment.")
        return 1

    logger.info("Started feature flag deployment number %s for configuration version %s.", deployment_number, new_version)
    write_github_output("status", "updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
