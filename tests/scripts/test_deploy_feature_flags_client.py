from unittest.mock import MagicMock

from scripts.deploy_feature_flags.app_config.client import validate_new_version


def test_validate_new_version_calls_validate_configuration_with_expected_arguments() -> None:
    client = MagicMock()

    validate_new_version(client, "app-1", "profile-1", 3)

    client.validate_configuration.assert_called_once_with(
        ApplicationId="app-1",
        ConfigurationProfileId="profile-1",
        ConfigurationVersion="3",
    )
