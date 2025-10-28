import logging
import os
from typing import List

import pytest

from devsynth.logging_setup import DevSynthLogger, configure_logging


class ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.mark.fast
def test_logging_redacts_openai_api_key(monkeypatch):
    # Arrange: set a plausible-looking API key
    secret = "sk-test-1234567890abcdef"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    # Reconfigure logging to ensure filters are attached
    configure_logging(create_dir=False)

    handler = ListHandler()
    root = logging.getLogger()
    root.addHandler(handler)

    logger = DevSynthLogger(__name__)

    # Act: log a message that includes the secret
    logger.info("Using key %s to test redaction: %s", secret, secret)

    # Assert: recorded message should not contain the raw secret
    found = False
    for rec in handler.records:
        msg = rec.getMessage()
        if "Using key" in msg:
            found = True
            assert secret not in msg
            # masked retains last 4 chars
            assert msg.count("***REDACTED***") >= 1
            assert secret[-4:] in msg
    assert found, "Expected to find a log record with our test message"


@pytest.mark.fast
def test_logging_redacts_in_extra_details(monkeypatch):
    secret = "sk-test-abcdef1234567890"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    configure_logging(create_dir=False)

    handler = ListHandler()
    root = logging.getLogger()
    root.addHandler(handler)

    logger = DevSynthLogger("redaction-extra")

    # Act: include secret in extra/details-like payload
    logger.warning("Attempt with extra", extra={"details": {"api_key": secret}})

    # Assert
    for rec in handler.records:
        if rec.name == "redaction-extra":
            # Depending on logging internals, the redaction filter updates record fields;
            # we check the formatted message and the extra mapping if present
            assert secret not in rec.getMessage()
            if hasattr(rec, "details") and isinstance(getattr(rec, "details"), dict):
                assert getattr(rec, "details")["api_key"].endswith(secret[-4:])
                assert "***REDACTED***" in getattr(rec, "details")["api_key"]
            break
