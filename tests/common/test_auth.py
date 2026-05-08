from unittest.mock import MagicMock, patch

import pytest

from common.auth import UserAuthorisationResult, get_user_info, is_authorised_user
from common.services.exceptions import MissingAuthTokenError

TEST_TOKEN = "test.jwt.token"  # noqa: S105
TEST_EMAIL = "user@example.com"


def _make_settings(environment: str = "development") -> MagicMock:
    settings = MagicMock()
    settings.ENVIRONMENT = environment
    return settings


class TestGetUserInfo:
    def test_returns_mock_user_in_local_environment(self):
        with patch("common.auth.settings", _make_settings("local")):
            result = get_user_info(None)

        assert result.email == "test@test.co.uk"
        assert result.is_authorised is True
        assert result.auth_reason == "LOCAL_TESTING"

    def test_raises_when_token_is_none(self):
        with patch("common.auth.settings", _make_settings()), pytest.raises(MissingAuthTokenError):
            get_user_info(None)

    def test_raises_when_token_is_empty(self):
        with patch("common.auth.settings", _make_settings()), pytest.raises(MissingAuthTokenError):
            get_user_info("")

    def test_returns_authorised_result_when_jwt_contains_email(self):
        with (
            patch("common.auth.settings", _make_settings()),
            patch("common.auth._verify_and_decode_alb_jwt", return_value={"email": TEST_EMAIL}),
        ):
            result = get_user_info(TEST_TOKEN)

        assert result.email == TEST_EMAIL
        assert result.is_authorised is True

    def test_propagates_exception_when_verifier_raises(self):
        with (
            patch("common.auth.settings", _make_settings()),
            patch("common.auth._verify_and_decode_alb_jwt", side_effect=ValueError("bad signature")),
            pytest.raises(ValueError, match="bad signature"),
        ):
            get_user_info(TEST_TOKEN)

    def test_propagates_exception_when_payload_has_no_email(self):
        with (
            patch("common.auth.settings", _make_settings()),
            patch("common.auth._verify_and_decode_alb_jwt", return_value={}),
            pytest.raises(ValueError, match="No email found"),
        ):
            get_user_info(TEST_TOKEN)


class TestIsAuthorisedUser:
    def test_returns_true_when_user_is_authorised(self):
        authorised_result = UserAuthorisationResult(email=TEST_EMAIL, is_authorised=True)
        with patch("common.auth.get_user_info", return_value=authorised_result):
            assert is_authorised_user(TEST_TOKEN) is True

    def test_returns_false_when_exception_is_raised(self):
        with patch("common.auth.get_user_info", side_effect=Exception("auth error")):
            assert is_authorised_user(TEST_TOKEN) is False
