"""Shared helpers for reconciling feature flag content and writing GitHub Actions step outputs."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# AWS-managed audit fields that AppConfig may stamp onto flags/values. They aren't part of
# authored content,ignored when reconciling to avoid spurious "changes detected".
IGNORED_KEYS = {"_createdAt", "_updatedAt"}


def strip_ignored_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: strip_ignored_keys(v) for k, v in value.items() if k not in IGNORED_KEYS}
    if isinstance(value, list):
        return [strip_ignored_keys(item) for item in value]
    return value


def write_github_output(name: str, value: str) -> None:
    """Write a `name=value` pair to $GITHUB_OUTPUT if running in GitHub Actions, otherwise no-op."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        return
    with Path(github_output).open("a") as f:
        f.write(f"{name}={value}\n")


def validate_required_args(args: argparse.Namespace) -> None:
    """Exit with status=error if any required argument ended up empty (e.g. from an empty env var).
    `argparse`'s own `required` check only tests whether the env var is *set*, not whether its
    value is non-empty. This function checks for empty values and reports them as errors.
    """
    required_fields = ["application_id", "environment_id", "configuration_profile_id", "deployment_strategy_id"]
    missing = [field for field in required_fields if not getattr(args, field)]
    if missing:
        logger.error("Missing required argument(s): %s", ", ".join(missing))
        write_github_output("status", "error")
        sys.exit(1)
