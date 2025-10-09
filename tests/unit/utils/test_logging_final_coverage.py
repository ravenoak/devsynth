"""Final coverage tests to reach >90% for devsynth.utils.logging module.

ReqID: UT-UTILS-LOG-FINAL
"""

import logging
import sys
from types import TracebackType

import pytest

from devsynth.utils.logging import DevSynthLogger, get_logger, setup_logging


@pytest.mark.fast
def test_dev_synth_logger_exc_info_baseexception_direct():
    """Test DevSynthLogger with BaseException instance to hit lines 31-35.

    ReqID: UT-UTILS-LOG-FINAL-01
    """
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Create a BaseException instance directly
    exc = ValueError("direct exception")

    # Test with BaseException instance - this should hit lines 31-35
    logger.error("msg with BaseException", exc_info=exc)

    # Verify the log was created with exc_info
    assert any(r.exc_info for r in logs if r.msg == "msg with BaseException")
    log_record = next(r for r in logs if r.msg == "msg with BaseException")
    assert log_record.exc_info[0] == ValueError
    assert str(log_record.exc_info[1]) == "direct exception"


@pytest.mark.fast
def test_dev_synth_logger_exc_info_true_with_active_exception():
    """Test DevSynthLogger with exc_info=True while exception is active to hit lines 37-38.

    ReqID: UT-UTILS-LOG-FINAL-02
    """
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Test with exc_info=True while exception is active - should hit lines 37-38
    try:
        raise RuntimeError("active exception")
    except RuntimeError:
        logger.error("msg with active exc_info=True", exc_info=True)

    # Verify the log was created with exc_info
    assert any(r.exc_info for r in logs if r.msg == "msg with active exc_info=True")
    log_record = next(r for r in logs if r.msg == "msg with active exc_info=True")
    assert log_record.exc_info[0] == RuntimeError
    assert str(log_record.exc_info[1]) == "active exception"


@pytest.mark.fast
def test_dev_synth_logger_exc_info_none_and_false_explicit():
    """Test DevSynthLogger with explicit None and False to hit line 40.

    ReqID: UT-UTILS-LOG-FINAL-03
    """
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Test with explicit None - should hit line 40
    logger.info("msg with None", exc_info=None)

    # Test with explicit False - should hit line 40
    logger.info("msg with False", exc_info=False)

    # Both should have no exc_info
    for msg in ["msg with None", "msg with False"]:
        log_record = next(r for r in logs if r.msg == msg)
        assert log_record.exc_info is None


@pytest.mark.fast
def test_dev_synth_logger_invalid_exc_info_to_hit_line_48():
    """Test DevSynthLogger with various invalid exc_info to hit line 48.

    ReqID: UT-UTILS-LOG-FINAL-04
    """
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Test with various invalid types - should hit line 48
    invalid_values = [
        "string",
        123,
        [],
        {},
        (1,),  # tuple too short
        (1, 2),  # tuple too short
        (1, 2, 3, 4),  # tuple too long
        object(),
    ]

    for i, invalid_value in enumerate(invalid_values):
        logger.warning(f"invalid{i}", exc_info=invalid_value)  # type: ignore[arg-type]

    # All should have no exc_info (normalized to None on line 48)
    for i in range(len(invalid_values)):
        log_record = next(r for r in logs if r.msg == f"invalid{i}")
        assert log_record.exc_info is None


@pytest.mark.fast
def test_get_logger_function_direct_call():
    """Test get_logger function directly to ensure line 55 coverage.

    ReqID: UT-UTILS-LOG-FINAL-05
    """
    # Direct call to get_logger - should hit line 55
    logger = get_logger("direct.test.logger")

    assert isinstance(logger, DevSynthLogger)
    assert logger.logger.name == "direct.test.logger"


@pytest.mark.fast
def test_setup_logging_function_direct_calls(monkeypatch):
    """Test setup_logging function directly to ensure lines 60-61 coverage.

    ReqID: UT-UTILS-LOG-FINAL-06
    """
    configure_calls = []

    def mock_configure_logging(level=None):  # noqa: ANN001
        configure_calls.append(level)

    import devsynth.utils.logging as L

    monkeypatch.setattr(L, "configure_logging", mock_configure_logging)

    # Direct call to setup_logging - should hit lines 60-61
    logger = setup_logging("direct.setup.test", log_level="WARNING")

    assert isinstance(logger, DevSynthLogger)
    assert logger.logger.name == "direct.setup.test"
    assert "WARNING" in configure_calls


@pytest.mark.fast
def test_dev_synth_logger_with_kwargs():
    """Test DevSynthLogger with additional kwargs to ensure complete coverage.

    ReqID: UT-UTILS-LOG-FINAL-07
    """
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Test with various kwargs
    logger.error("msg with kwargs", exc_info=None, extra={"key": "value"})

    log_record = next(r for r in logs if r.msg == "msg with kwargs")
    assert log_record.exc_info is None
    assert hasattr(log_record, "key")
    assert log_record.key == "value"
