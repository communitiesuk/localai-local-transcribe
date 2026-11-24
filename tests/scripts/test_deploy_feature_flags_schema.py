import jsonschema
import pytest

from scripts.deploy_feature_flags.schema import validate_feature_flags


def test_validate_feature_flags_accepts_valid_content() -> None:
    content = {
        "version": "1",
        "flags": {"my-flag": {"name": "My Flag"}},
        "values": {"my-flag": {"enabled": True}},
    }

    validate_feature_flags(content)


def test_validate_feature_flags_rejects_invalid_flag_key() -> None:
    content = {
        "version": "1",
        "flags": {"My-Flag": {"name": "My Flag"}},
        "values": {},
    }

    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_feature_flags(content)
