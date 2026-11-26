import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from scripts.deploy_feature_flags.main import main


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


@patch("scripts.deploy_feature_flags.main.write_github_output")
@patch("scripts.deploy_feature_flags.main.boto3")
@patch("scripts.deploy_feature_flags.main.get_deployed_version")
@patch("scripts.deploy_feature_flags.main.parse_args")
def test_main_reports_error_status_when_reading_deployed_version_fails(
    mock_parse_args: MagicMock,
    mock_get_deployed_version: MagicMock,
    mock_boto3: MagicMock,
    mock_write_github_output: MagicMock,
    tmp_path: Path,
) -> None:
    feature_flags_file = tmp_path / "feature_flags.json"
    feature_flags_file.write_text("{}")
    mock_parse_args.return_value = _make_args(feature_flags_file=str(feature_flags_file))
    mock_get_deployed_version.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Invalid ApplicationId"}}, "ListDeployments"
    )

    result = main()

    assert result == 1
    mock_boto3.client.assert_called_once_with("appconfig")
    mock_write_github_output.assert_called_once_with("status", "error")
