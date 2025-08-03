"""Tests for the devsynth.logger module."""

from __future__ import annotations

import importlib
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import devsynth.logger as ds_logger


def test_configure_logging_creates_rotating_handler(tmp_path, monkeypatch):
    """configure_logging should set up a rotating file handler."""
    # Reload module to reset internal state
    ds_logger = importlib.reload(ds_logger)

    # Run in temporary directory so test logs are isolated
    monkeypatch.chdir(tmp_path)

    # Ensure root logger has no handlers
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)

    ds_logger.configure_logging(log_level=logging.DEBUG, max_bytes=200, backup_count=1)

    log_path = Path("logs") / "devsynth.log"
    assert log_path.exists(), "log file should be created"

    handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
    assert handlers, "rotating file handler not configured"
    assert root.level == logging.DEBUG
