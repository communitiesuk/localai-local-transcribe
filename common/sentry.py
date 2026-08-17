from sentry_sdk.types import Event, Hint

REDACTED = "[REDACTED]"


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

    return event
