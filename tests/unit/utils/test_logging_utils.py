import logging

import pytest

from devsynth.utils.logging import DevSynthLogger, get_logger, setup_logging


@pytest.mark.fast
def test_dev_synth_logger_normalizes_exc_info_tuple_and_exception(monkeypatch):
    logs = []

    class Handler(logging.Handler):
        def emit(self, record):  # noqa: ANN001
            logs.append(record)

    logger = DevSynthLogger(__name__)
    logger.logger.setLevel(logging.DEBUG)
    handler = Handler()
    logger.logger.addHandler(handler)

    # Case 1: exc_info=True when an exception is active
    try:
        raise ValueError("boom")
    except ValueError:
        logger.error("msg1", exc_info=True)

    # Case 2: exc_info is the exception instance
    try:
        raise RuntimeError("kapow")
    except RuntimeError as e:
        logger.error("msg2", exc_info=e)

    # Case 3: exc_info garbage should be ignored (becomes None)
    logger.warning("msg3", exc_info="nonsense")  # type: ignore[arg-type]

    assert any(r.exc_info for r in logs if r.msg == "msg1")
    assert any(r.exc_info for r in logs if r.msg == "msg2")
    # msg3 should have no exc_info attached
    assert any(r.exc_info is None for r in logs if r.msg == "msg3")


@pytest.mark.fast
def test_setup_logging_calls_configure_logging(monkeypatch):
    called = {}

    def fake_configure_logging(level=None):  # noqa: ANN001
        called["ok"] = level if level is not None else True

    import devsynth.utils.logging as L

    monkeypatch.setattr(L, "configure_logging", fake_configure_logging)
    log = setup_logging("x", log_level="INFO")
    assert isinstance(log, DevSynthLogger)
    assert called["ok"] == "INFO"


@pytest.mark.fast
def test_get_logger_returns_dev_synth_logger_instance():
    log = get_logger("demo")
    assert isinstance(log, DevSynthLogger)
