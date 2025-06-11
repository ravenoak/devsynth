import logging
from devsynth.logging_setup import (
    configure_logging,
    get_logger,
    set_request_context,
    clear_request_context,
)
from _pytest.logging import LogCaptureHandler


def test_log_records_include_request_context(caplog, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    configure_logging(create_dir=False)
    logger = get_logger(__name__)
    handler = LogCaptureHandler()
    logging.getLogger().addHandler(handler)
    set_request_context("req-123", "EXPAND")
    logger.info("hello")
    clear_request_context()
    logging.getLogger().removeHandler(handler)
    assert ("req-123", "EXPAND") in [(rec.request_id, rec.phase) for rec in handler.records]
