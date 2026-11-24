from scripts.deploy_feature_flags.helpers import strip_ignored_keys


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
