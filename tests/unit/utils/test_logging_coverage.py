"""Additional tests to achieve >90% coverage for devsynth.utils.logging module.

ReqID: UT-UTILS-LOG-COV
"""

import logging
import sys
from types import TracebackType

import pytest

from devsynth.utils.logging import DevSynthLogger, get_logger, setup_logging


@pytest.mark.fast
def test_dev_synth_logger_handles_tuple_exc_info():
    """Test DevSynthLogger with 3-tuple exc_info to cover line 42.

    ReqID: UT-UTILS-LOG-COV-01
    """
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Create a proper exc_info tuple
    try:
        raise ValueError("test exception")
    except ValueError:
        exc_type, exc_value, exc_traceback = sys.exc_info()

    # Test with 3-tuple exc_info - this should hit line 42
    exc_info_tuple = (exc_type, exc_value, exc_traceback)
    logger.error("msg with tuple exc_info", exc_info=exc_info_tuple)

    # Verify the log was created with exc_info
    assert any(r.exc_info for r in logs if r.msg == "msg with tuple exc_info")
    # Verify the exc_info tuple was normalized correctly
    log_record = next(r for r in logs if r.msg == "msg with tuple exc_info")
    assert log_record.exc_info[0] == ValueError
    assert str(log_record.exc_info[1]) == "test exception"


@pytest.mark.fast
def test_dev_synth_logger_handles_invalid_exc_info():
    """Test DevSynthLogger with invalid exc_info types to cover line 40.

    ReqID: UT-UTILS-LOG-COV-02
    """
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Test with invalid exc_info types - these should hit line 40 (normalized_exc = None)
    invalid_exc_infos = [
        "invalid_string",  # string
        123,  # integer
        [],  # empty list
        (1, 2),  # wrong tuple size
        {"error": "dict"},  # dict
    ]

    for i, invalid_exc_info in enumerate(invalid_exc_infos):
        logger.warning(f"msg{i}", exc_info=invalid_exc_info)  # type: ignore[arg-type]

    # All should have no exc_info (normalized to None)
    for i in range(len(invalid_exc_infos)):
        log_record = next(r for r in logs if r.msg == f"msg{i}")
        assert log_record.exc_info is None


@pytest.mark.fast
def test_get_logger_returns_correct_instance():
    """Test get_logger function directly to ensure line 55 coverage.

    ReqID: UT-UTILS-LOG-COV-03
    """
    logger_name = "test.logger.name"
    logger = get_logger(logger_name)

    assert isinstance(logger, DevSynthLogger)
    assert logger.logger.name == logger_name


@pytest.mark.fast
def test_setup_logging_with_different_log_levels(monkeypatch):
    """Test setup_logging function with various log levels to ensure lines 60-61 coverage.

    ReqID: UT-UTILS-LOG-COV-04
    """
    called_with = []

    def mock_configure_logging(level=None):  # noqa: ANN001
        called_with.append(level)

    import devsynth.utils.logging as L

    monkeypatch.setattr(L, "configure_logging", mock_configure_logging)

    # Test with string log level
    logger1 = setup_logging("test.logger1", log_level="DEBUG")
    assert isinstance(logger1, DevSynthLogger)
    assert logger1.logger.name == "test.logger1"
    assert "DEBUG" in called_with

    # Test with integer log level
    logger2 = setup_logging("test.logger2", log_level=logging.WARNING)
    assert isinstance(logger2, DevSynthLogger)
    assert logger2.logger.name == "test.logger2"
    assert logging.WARNING in called_with

    # Test with None log level
    logger3 = setup_logging("test.logger3", log_level=None)
    assert isinstance(logger3, DevSynthLogger)
    assert logger3.logger.name == "test.logger3"
    assert None in called_with


@pytest.mark.fast
def test_dev_synth_logger_handles_false_exc_info():
    """Test DevSynthLogger with exc_info=False to ensure complete coverage.

    ReqID: UT-UTILS-LOG-COV-05
    """
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Test with exc_info=False
    logger.info("test message", exc_info=False)

    log_record = next(r for r in logs if r.msg == "test message")
    assert log_record.exc_info is None


@pytest.mark.fast
def test_dev_synth_logger_handles_none_exc_info():
    """Test DevSynthLogger with exc_info=None to ensure complete coverage.

    ReqID: UT-UTILS-LOG-COV-06
    """
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Test with exc_info=None (explicit)
    logger.info("test message none", exc_info=None)

    log_record = next(r for r in logs if r.msg == "test message none")
    assert log_record.exc_info is None
