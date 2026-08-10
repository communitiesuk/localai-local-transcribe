import logging
import re

from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.enrichment_types import ExecutionEnvironmentType
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat


class SensitiveDataSanitizerFilter(logging.Filter):
    """Filter to redact sensitive data from logs as a defence-in-depth measure."""

    PATTERNS = [
        (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[REDACTED_EMAIL]"),
        (re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b"), "[REDACTED_POSTCODE]"),
    ]

    def _scrub(self, value: object) -> object:
        if isinstance(value, str):
            for pattern, replacement in self.PATTERNS:
                value = pattern.sub(replacement, value)
        return value

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._scrub(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._scrub(v) for k, v in record.args.items()}
            else:
                record.args = tuple(self._scrub(a) for a in record.args)
        return True


def setup_logger() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger().addFilter(SensitiveDataSanitizerFilter())


def setup_structured_logger(
    level: str, execution_environment: ExecutionEnvironmentType, logging_format: LogOutputFormat
) -> StructuredLogger:
    return StructuredLogger(
        level=level or "info",
        options={
            "execution_environment": execution_environment,
            "log_format": logging_format,
        },
    )
