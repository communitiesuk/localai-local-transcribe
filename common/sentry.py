from typing import Any
from sentry_sdk.hub import Hub
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.types import Event, Hint


REDACTED = "[REDACTED]"
TRANSCRIPT_KEYS = ("transcript", "dialogue_entries", "dialogue entries")


def _looks_like_dialogue_entries(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if not all(isinstance(item, dict) for item in value):
        return False

    dialogue_keys = {"speaker", "text", "utterance", "start", "end", "timestamp"}
    return any(bool(dialogue_keys.intersection({str(k).lower() for k in item})) for item in value)


def scrub_sensitive_fields(event: Event, hint: Hint) -> Event | None:  # noqa: ARG001
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("data", None)
        request.pop("cookies", None)

        headers = request.get("headers")
        if isinstance(headers, dict):
            for header in list(headers.keys()):
                if str(header).lower() in {"cookie", "set-cookie"}:
                    headers[header] = REDACTED

    extra = event.get("extra")
    if isinstance(extra, dict):
        for key in list(extra.keys()):
            value = extra[key]
            key_name = str(key).lower()
            if any(fragment in key_name for fragment in TRANSCRIPT_KEYS) or _looks_like_dialogue_entries(value):
                extra.pop(key, None)

    return event
