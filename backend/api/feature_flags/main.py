"""CLI entrypoint for manually reading AppConfig feature flag data.

Useful for local testing of the boto3 fallback path without needing to hit the HTTP route.

Usage:
    poetry run python -m backend.api.feature_flags.main                     # full config JSON
    poetry run python -m backend.api.feature_flags.main offline_recordings  # single flag's enabled value
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging

from .client import FeatureFlagsNotConfiguredError, get_feature_flag_enabled, get_feature_flags_config

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read AppConfig feature flag data.")
    parser.add_argument(
        "flag_name",
        nargs="?",
        default=None,
        help="Name of a single feature flag to read, e.g. offline_recordings. "
        "If omitted, prints the full configuration JSON.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    try:
        if args.flag_name is None:
            config = asyncio.run(get_feature_flags_config())
            print(json.dumps(config, indent=2))  # noqa: T201
        else:
            enabled = asyncio.run(get_feature_flag_enabled(args.flag_name))
            logger.info("%s: %s", args.flag_name, enabled)
    except FeatureFlagsNotConfiguredError as e:
        logger.error("Could not read feature flags: %s", e)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
