import logging
import re
from collections.abc import Mapping, Sequence
from typing import ClassVar


class SensitiveDataSanitizerFilter(logging.Filter):
    """Filter to redact sensitive data from logs as a defence-in-depth measure."""

    PATTERNS: ClassVar[list[tuple[re.Pattern[str], str]]] = [
        (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[REDACTED_EMAIL]"),
        (re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b"), "[REDACTED_POSTCODE]"),
    ]

    def _scrub(self, value: object) -> object:
        return scrub_sensitive_data(value)

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._scrub(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._scrub(v) for k, v in record.args.items()}
            else:
                record.args = tuple(self._scrub(a) for a in record.args)
        return True


def scrub_sensitive_data(value: object) -> object:
    if isinstance(value, str):
        scrubbed = value
        for pattern, replacement in SensitiveDataSanitizerFilter.PATTERNS:
            scrubbed = pattern.sub(replacement, scrubbed)
        return scrubbed

    if isinstance(value, Mapping):
        return {k: scrub_sensitive_data(v) for k, v in value.items()}

    if isinstance(value, tuple):
        return tuple(scrub_sensitive_data(item) for item in value)

    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [scrub_sensitive_data(item) for item in value]

    return value


def setup_logger() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(SensitiveDataSanitizerFilter())


