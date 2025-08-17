import pytest

from devsynth.logging_setup import DevSynthLogger as _BaseLogger
from devsynth.utils.logging import DevSynthLogger, setup_logging


@pytest.mark.fast
def test_setup_logging_returns_project_logger(monkeypatch):
    """setup_logging configures logging and returns a project logger."""
    captured = {}

    def fake_config(level):
        captured["level"] = level

    monkeypatch.setattr("devsynth.utils.logging.configure_logging", fake_config)
    logger = setup_logging("name", log_level=10)
    assert captured["level"] == 10
    assert isinstance(logger, DevSynthLogger)


@pytest.mark.fast
def test_log_normalizes_exception(monkeypatch):
    """DevSynthLogger converts exceptions to exc_info tuples."""
    logger = DevSynthLogger("test")
    records = {}

    def fake_log(self, level, msg, *args, **kwargs):
        records["exc_info"] = kwargs.get("exc_info")

    monkeypatch.setattr(_BaseLogger, "_log", fake_log)
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        logger.error("oops", exc_info=exc)
        captured = exc

    assert isinstance(records["exc_info"], tuple)
    assert records["exc_info"][1] is captured
