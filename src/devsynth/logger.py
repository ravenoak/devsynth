"""Central logging configuration for DevSynth components.

This module sets up a shared logging configuration so that all parts of the
system emit logs to ``logs/devsynth.log``.  Logs are rotated automatically and
the log level can be controlled programmatically or via the
``DEVSYNTH_LOG_LEVEL`` environment variable.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from devsynth.logging_setup import (
    DevSynthLogger,
    JSONFormatter,
    clear_request_context,
    set_request_context,
)

DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "devsynth.log"

_configured = False


def configure_logging(
    log_level: int | str | None = None,
    *,
    max_bytes: int = 1_000_000,
    backup_count: int = 5,
) -> None:
    """Configure the root logger with file rotation and console output.

    Args:
        log_level: Logging level or name.  If ``None`` the ``DEVSYNTH_LOG_LEVEL``
            environment variable is consulted and defaults to ``INFO``.
        max_bytes: Maximum size of the log file before rotation occurs.
        backup_count: Number of rotated log files to keep.
    """
    global _configured
    if _configured:
        return

    if isinstance(log_level, str):
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        env_level = os.getenv("DEVSYNTH_LOG_LEVEL", "INFO").upper()
        level = (
            log_level
            if log_level is not None
            else getattr(logging, env_level, logging.INFO)
        )

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    no_file_logging = os.getenv("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in {
        "1",
        "true",
        "yes",
    }
    if not no_file_logging:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(JSONFormatter())
        root.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> DevSynthLogger:
    """Return a :class:`DevSynthLogger` for ``name``.

    The logging system is configured on first use.
    """
    if not _configured:
        configure_logging()
    return DevSynthLogger(name)


def setup_logging(name: str, log_level: int | str | None = None) -> DevSynthLogger:
    """Configure logging and return a logger for ``name``.

    This helper mirrors :func:`get_logger` but allows the caller to provide a
    ``log_level`` for initial configuration.
    """
    configure_logging(log_level)
    return DevSynthLogger(name)


__all__ = [
    "configure_logging",
    "get_logger",
    "setup_logging",
    "DevSynthLogger",
    "set_request_context",
    "clear_request_context",
]
