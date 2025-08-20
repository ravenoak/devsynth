import logging

import pytest

from devsynth.logger import DevSynthLogger
from devsynth.logging_setup import DevSynthLogger as BaseDevSynthLogger

pytestmark = pytest.mark.fast


def test_log_exception_object_normalized(monkeypatch):
    """Exception objects become ``(type, value, traceback)`` tuples.

    ReqID: LOG-1"""
    captured: dict[str, object] = {}

    def fake_log(self, level, msg, *args, **kwargs):
        captured["exc_info"] = kwargs.get("exc_info")

    monkeypatch.setattr(BaseDevSynthLogger, "_log", fake_log)
    logger = DevSynthLogger("test")
    err = ValueError("boom")
    logger._log(logging.ERROR, "msg", exc_info=err)
    exc_info = captured["exc_info"]
    assert isinstance(exc_info, tuple)
    assert exc_info[0] is ValueError and exc_info[1] is err


def test_log_true_uses_current_exception(monkeypatch):
    """Passing ``exc_info=True`` attaches the active exception.

    ReqID: LOG-2"""
    captured: dict[str, object] = {}

    def fake_log(self, level, msg, *args, **kwargs):
        captured["exc_info"] = kwargs.get("exc_info")

    monkeypatch.setattr(BaseDevSynthLogger, "_log", fake_log)
    logger = DevSynthLogger("test")
    try:
        raise RuntimeError("fail")
    except RuntimeError:
        logger._log(logging.ERROR, "msg", exc_info=True)
    exc_info = captured["exc_info"]
    assert isinstance(exc_info, tuple)
    assert exc_info[0] is RuntimeError


def test_log_invalid_exc_info_dropped(monkeypatch):
    """Invalid ``exc_info`` values are ignored.

    ReqID: LOG-3"""
    captured: dict[str, object] = {}

    def fake_log(self, level, msg, *args, **kwargs):
        captured["exc_info"] = kwargs.get("exc_info")

    monkeypatch.setattr(BaseDevSynthLogger, "_log", fake_log)
    logger = DevSynthLogger("test")
    logger._log(logging.ERROR, "msg", exc_info="bad")
    assert captured["exc_info"] is None
