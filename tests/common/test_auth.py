from unittest.mock import MagicMock, patch

import jwt
import pytest

import common.auth
from common.auth import (
    UserAuthorisationResult,
    _get_public_key,
    _verify_and_decode_alb_jwt,
    get_user_info,
    is_authorised_user,
)
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


class TestVerifyAndDecodeAlbJwt:
    TEST_ALB_ARN = "arn:aws:elasticloadbalancing:eu-west-2:123456789012:loadbalancer/app/test/abc"
    TEST_KID = "test-kid"
    TEST_ISSUER = "https://issuer.example.com"

    def _make_settings(self, alb_arn: str | None = None) -> MagicMock:
        settings = MagicMock()
        settings.ALB_ARN = alb_arn or self.TEST_ALB_ARN
        settings.OIDC_ISSUER = self.TEST_ISSUER
        return settings

    def test_raises_when_signer_does_not_match_alb_arn(self):
        with (
            patch("common.auth.settings", self._make_settings()),
            patch("common.auth.jwt.get_unverified_header", return_value={"signer": "wrong-arn", "kid": self.TEST_KID}),
            pytest.raises(ValueError, match="JWT signer does not match expected ALB ARN"),
        ):
            _verify_and_decode_alb_jwt("tok")

    def test_raises_when_signer_is_absent(self):
        with (
            patch("common.auth.settings", self._make_settings()),
            patch("common.auth.jwt.get_unverified_header", return_value={"kid": self.TEST_KID}),
            pytest.raises(ValueError, match="JWT signer does not match expected ALB ARN"),
        ):
            _verify_and_decode_alb_jwt("tok")

    def test_returns_decoded_payload_on_valid_token(self):
        expected_payload = {"email": TEST_EMAIL, "sub": "user123"}
        with (
            patch("common.auth.settings", self._make_settings()),
            patch(
                "common.auth.jwt.get_unverified_header",
                return_value={"signer": self.TEST_ALB_ARN, "kid": self.TEST_KID},
            ),
            patch("common.auth._get_public_key", return_value="fake-key") as mock_get_key,
            patch("common.auth.jwt.decode", return_value=expected_payload) as mock_decode,
        ):
            result = _verify_and_decode_alb_jwt("tok")

        assert result == expected_payload
        mock_get_key.assert_called_once_with(self.TEST_KID)
        mock_decode.assert_called_once_with("tok", "fake-key", algorithms=["ES256"], issuer=self.TEST_ISSUER)

    def test_retries_with_fresh_key_on_decode_error(self):
        expected_payload = {"email": TEST_EMAIL}
        with (
            patch("common.auth.settings", self._make_settings()),
            patch(
                "common.auth.jwt.get_unverified_header",
                return_value={"signer": self.TEST_ALB_ARN, "kid": self.TEST_KID},
            ),
            patch("common.auth._get_public_key", side_effect=["stale-key", "fresh-key"]) as mock_get_key,
            patch("common.auth.jwt.decode", side_effect=[jwt.DecodeError("bad"), expected_payload]),
        ):
            result = _verify_and_decode_alb_jwt("tok")

        assert result == expected_payload
        assert mock_get_key.call_count == 2

    def test_propagates_decode_error_when_retry_also_fails(self):
        with (
            patch("common.auth.settings", self._make_settings()),
            patch(
                "common.auth.jwt.get_unverified_header",
                return_value={"signer": self.TEST_ALB_ARN, "kid": self.TEST_KID},
            ),
            patch("common.auth._get_public_key", return_value="fake-key"),
            patch("common.auth.jwt.decode", side_effect=jwt.DecodeError("bad")),
            pytest.raises(jwt.DecodeError),
        ):
            _verify_and_decode_alb_jwt("tok")


class TestGetPublicKey:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        common.auth._public_key_cache.clear()  # noqa: SLF001
        yield
        common.auth._public_key_cache.clear()  # noqa: SLF001

    def _make_settings(self, aws_region: str = "eu-west-2") -> MagicMock:
        settings = MagicMock()
        settings.AWS_REGION = aws_region
        return settings

    def test_fetches_key_from_correct_aws_url(self):
        mock_response = MagicMock()
        mock_response.text = "pem-data"
        with (
            patch("common.auth.settings", self._make_settings()),
            patch("common.auth.requests.get", return_value=mock_response) as mock_get,
        ):
            result = _get_public_key("abc123")

        mock_get.assert_called_once_with(
            "https://public-keys.auth.elb.eu-west-2.amazonaws.com/abc123",
            timeout=5,
        )
        assert result == "pem-data"

    def test_caches_key_after_first_fetch(self):
        mock_response = MagicMock()
        mock_response.text = "pem-data"
        with (
            patch("common.auth.settings", self._make_settings()),
            patch("common.auth.requests.get", return_value=mock_response) as mock_get,
        ):
            _get_public_key("abc123")
            _get_public_key("abc123")

        mock_get.assert_called_once()

    def test_returns_cached_key_without_http_call(self):
        common.auth._public_key_cache["abc123"] = "cached-pem"  # noqa: SLF001
        with patch("common.auth.requests.get") as mock_get:
            result = _get_public_key("abc123")

        mock_get.assert_not_called()
        assert result == "cached-pem"
