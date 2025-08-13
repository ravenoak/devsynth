import logging

from _pytest.logging import LogCaptureHandler

from devsynth.logging_setup import (
    clear_request_context,
    configure_logging,
    get_logger,
    set_request_context,
)


def test_log_records_include_request_context_succeeds(caplog, monkeypatch):
    """Test that log records include request context succeeds.

    ReqID: N/A"""
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    configure_logging(create_dir=False)
    logger = get_logger(__name__)
    handler = LogCaptureHandler()
    logging.getLogger().addHandler(handler)
    set_request_context("req-123", "EXPAND")
    logger.info("hello")
    clear_request_context()
    logging.getLogger().removeHandler(handler)
    assert ("req-123", "EXPAND") in [
        (rec.request_id, rec.phase) for rec in handler.records
    ]


def test_exc_info_passes_through_succeeds(caplog, monkeypatch):
    """DevSynthLogger should forward exc_info to logging."""

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    configure_logging(create_dir=False)
    logger = get_logger(__name__)
    handler = LogCaptureHandler()
    logging.getLogger().addHandler(handler)
    try:
        raise ValueError("boom")
    except ValueError as err:  # pragma: no cover - demonstration
        logger.error("oops", exc_info=err)
    logging.getLogger().removeHandler(handler)
    record = handler.records[0]
    assert record.exc_info and record.exc_info[0] is ValueError


def test_exc_info_true_uses_current_exception(monkeypatch):
    """Passing exc_info=True attaches the active exception."""

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    configure_logging(create_dir=False)
    logger = get_logger(__name__)
    handler = LogCaptureHandler()
    logging.getLogger().addHandler(handler)
    try:
        1 / 0
    except ZeroDivisionError:  # pragma: no cover - demonstration
        logger.error("boom", exc_info=True)
    logging.getLogger().removeHandler(handler)
    record = handler.records[0]
    assert record.exc_info and record.exc_info[0] is ZeroDivisionError


def test_extra_kwargs_and_reserved_keys_safely_handled(monkeypatch):
    """Reserved keys in kwargs or extra should not raise errors."""

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    configure_logging(create_dir=False)
    logger = get_logger(__name__)
    handler = LogCaptureHandler()
    logging.getLogger().addHandler(handler)
    logger.info("hello", module="fake", extra={"module": "fake", "foo": "bar"})
    logging.getLogger().removeHandler(handler)
    record = handler.records[0]
    assert getattr(record, "foo") == "bar"
    assert record.module != "fake"
