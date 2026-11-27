import argparse
from unittest.mock import MagicMock, patch

import pytest

from scripts.deploy_feature_flags.helpers import strip_ignored_keys, validate_required_args


def _make_args(**overrides: str) -> argparse.Namespace:
    defaults = {
        "application_id": "app-1",
        "environment_id": "env-1",
        "configuration_profile_id": "profile-1",
        "deployment_strategy_id": "strategy-1",
        "feature_flags_file": "feature_flags.json",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_validate_required_args_passes_when_all_fields_populated() -> None:
    validate_required_args(_make_args())


@patch("scripts.deploy_feature_flags.helpers.write_github_output")
def test_validate_required_args_exits_with_error_status_on_empty_string_field(
    mock_write_github_output: MagicMock,
) -> None:
    # Simulates an env var that is set but empty (e.g. APPCONFIG_APPLICATION_ID=""), which
    # argparse's own `required` check does not catch since it only tests presence, not truthiness.
    args = _make_args(application_id="")

    with pytest.raises(SystemExit) as exc_info:
        validate_required_args(args)

    assert exc_info.value.code == 1
    mock_write_github_output.assert_called_once_with("status", "error")


def test_strip_ignored_keys_equal_when_only_audit_fields_differ() -> None:
    deployed = {
        "flags": {
            "my-flag": {
                "name": "my-flag",
                "_createdAt": "2024-01-01T00:00:00Z",
                "_updatedAt": "2024-06-01T00:00:00Z",
            }
        },
        "values": {"my-flag": {"enabled": True}},
        "version": "1",
    }
    local = {
        "flags": {"my-flag": {"name": "my-flag"}},
        "values": {"my-flag": {"enabled": True}},
        "version": "1",
    }

    assert strip_ignored_keys(deployed) == strip_ignored_keys(local)


def test_strip_ignored_keys_detects_real_content_difference() -> None:
    deployed = {
        "flags": {"my-flag": {"name": "my-flag", "_createdAt": "2024-01-01T00:00:00Z"}},
        "values": {"my-flag": {"enabled": True}},
        "version": "1",
    }
    local = {
        "flags": {"my-flag": {"name": "my-flag", "_createdAt": "2024-01-01T00:00:00Z"}},
        "values": {"my-flag": {"enabled": False}},
        "version": "1",
    }

    assert strip_ignored_keys(deployed) != strip_ignored_keys(local)
