from sentry_sdk.types import Event, Hint

from common.sentry import scrub_sensitive_fields


def test_scrub_sensitive_fields_removes_dialogue_entries_shaped_extra_payload() -> None:
    event: Event = {
        "extra": {
            "model_output": [
                {"speaker": "Agent", "text": "Hello there", "start": 0.0, "end": 1.2},
                {"speaker": "User", "text": "Hi", "start": 1.3, "end": 1.6},
            ],
            "safe_value": "kept",
        }
    }
    hint: Hint = {}

    scrubbed = scrub_sensitive_fields(event, hint)

    assert scrubbed is not None
    assert "model_output" not in scrubbed["extra"]
    assert scrubbed["extra"]["safe_value"] == "kept"
