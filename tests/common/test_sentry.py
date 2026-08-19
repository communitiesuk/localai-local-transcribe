from sentry_sdk.types import Event, Hint

from common.sentry import scrub_sensitive_fields


def test_scrub_sensitive_fields_removes_request_data_and_cookies() -> None:
    event: Event = {"request": {"data": {"password": "secret"}, "cookies": {"session": "abc"}, "url": "/upload"}}
    hint: Hint = {}

    scrubbed = scrub_sensitive_fields(event, hint)

    assert scrubbed is not None
    assert "data" not in scrubbed["request"]
    assert "cookies" not in scrubbed["request"]
    assert scrubbed["request"]["url"] == "/upload"


def test_scrub_sensitive_fields_redacts_cookie_headers() -> None:
    event: Event = {
        "request": {
            "headers": {
                "Cookie": "session=abc",
                "Set-Cookie": "session=xyz",
                "Content-Type": "application/json",
            }
        }
    }
    hint: Hint = {}

    scrubbed = scrub_sensitive_fields(event, hint)

    assert scrubbed is not None
    headers = scrubbed["request"]["headers"]
    assert headers["Cookie"] == "[REDACTED]"
    assert headers["Set-Cookie"] == "[REDACTED]"
    assert headers["Content-Type"] == "application/json"


def test_scrub_sensitive_fields_returns_event_unchanged_when_no_request() -> None:
    event: Event = {"level": "error"}
    hint: Hint = {}

    scrubbed = scrub_sensitive_fields(event, hint)

    assert scrubbed == {"level": "error"}
