import logging

import pytest

from common.logger import SensitiveDataSanitizerFilter, setup_logger


class CapturingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture()
def capturing_handler():
    """Add a capturing handler to the root logger before setup_logger() is called
    so that setup_logger()'s handler loop registers the sanitizer filter on it."""
    handler = CapturingHandler()
    root = logging.getLogger()
    root.addHandler(handler)
    yield handler
    root.removeHandler(handler)
    for f in list(handler.filters):
        if isinstance(f, SensitiveDataSanitizerFilter):
            handler.removeFilter(f)


class TestSetupLoggerRegistersFilter:
    def test_filter_is_added_to_handler(self, capturing_handler):
        setup_logger()
        assert any(isinstance(f, SensitiveDataSanitizerFilter) for f in capturing_handler.filters)


class TestSensitiveDataSanitizerFilterScrubsLogs:
    @pytest.fixture()
    def logger(self, capturing_handler):
        """Child logger that propagates to root so records pass through
        the capturing handler (and its registered sanitizer filter)."""
        setup_logger()
        child = logging.getLogger("test.scrub")
        child.setLevel(logging.DEBUG)
        child.propagate = True
        return child

    def test_email_in_message_is_redacted(self, logger, capturing_handler):
        logger.info("User email is user@example.com")
        assert "[REDACTED_EMAIL]" in capturing_handler.records[-1].getMessage()
        assert "user@example.com" not in capturing_handler.records[-1].getMessage()

    def test_postcode_in_message_is_redacted(self, logger, capturing_handler):
        logger.info("Address is SW1A 1AA")
        assert "[REDACTED_POSTCODE]" in capturing_handler.records[-1].getMessage()
        assert "SW1A 1AA" not in capturing_handler.records[-1].getMessage()

    def test_email_in_args_is_redacted(self, logger, capturing_handler):
        logger.info("Contact: %s", "user@example.com")
        assert "[REDACTED_EMAIL]" in capturing_handler.records[-1].getMessage()
        assert "user@example.com" not in capturing_handler.records[-1].getMessage()

    def test_postcode_in_dict_args_is_redacted(self, logger, capturing_handler):
        logger.info("Data: %(address)s", {"address": "EC1A 1BB"})
        assert "[REDACTED_POSTCODE]" in capturing_handler.records[-1].getMessage()

    def test_non_sensitive_message_is_unchanged(self, logger, capturing_handler):
        logger.info("Nothing sensitive here")
        assert capturing_handler.records[-1].getMessage() == "Nothing sensitive here"
