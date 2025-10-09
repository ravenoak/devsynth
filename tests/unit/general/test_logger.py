"""Tests for the devsynth.logger module."""

from __future__ import annotations

import importlib
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureHandler

import devsynth.logger as ds_logger

pytestmark = [pytest.mark.fast]


def test_configure_logging_creates_rotating_handler(tmp_path, monkeypatch):
    """configure_logging should set up a rotating file handler."""
    # Reload module to reset internal state
    module = importlib.reload(ds_logger)

    # Run in temporary directory so test logs are isolated
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")

    # Ensure root logger has no handlers
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)

    module.configure_logging(log_level=logging.DEBUG, max_bytes=200, backup_count=1)

    log_path = Path("logs") / "devsynth.log"
    assert log_path.exists(), "log file should be created"

    handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
    assert handlers, "rotating file handler not configured"
    assert root.level == logging.DEBUG


def test_dev_synth_logger_normalizes_exc_info(monkeypatch):
    """Bare exception instances should be converted into ``exc_info`` tuples."""
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    ds_logger.configure_logging()
    logger = ds_logger.get_logger(__name__)
    handler = LogCaptureHandler()
    logging.getLogger().addHandler(handler)
    try:
        raise RuntimeError("boom")
    except RuntimeError as err:  # pragma: no cover - demonstration
        logger.error("oops", exc_info=err)
    logging.getLogger().removeHandler(handler)
    record = handler.records[0]
    assert record.exc_info and record.exc_info[0] is RuntimeError
