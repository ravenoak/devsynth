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
from typing import Any, Dict

from devsynth.logging_setup import DevSynthLogger as _BaseDevSynthLogger
from devsynth.logging_setup import (
    JSONFormatter,
    clear_request_context,
    set_request_context,
)


class DevSynthLogger(_BaseDevSynthLogger):
    """Project-level logger that normalizes ``exc_info`` values.

    Some callers pass exception instances directly via ``exc_info`` which the
    standard :mod:`logging` package expects as a boolean or a ``(type, value,
    traceback)`` tuple.  This wrapper converts exception objects into the tuple
    form before delegating to the base implementation so stack traces are
    recorded correctly.  It also resolves ``exc_info=True`` to the active
    exception via :func:`sys.exc_info` to provide a consistent tuple for the
    base logger.
    """

    def _log(self, level: int, msg: str, *args, **kwargs) -> None:  # type: ignore[override]
        """Normalize ``exc_info`` and delegate to the base logger.

        The standard :mod:`logging` API expects ``exc_info`` to either be a
        boolean or a ``(type, value, traceback)`` tuple.  Some callers pass
        exception instances or other arbitrary objects which can trigger
        ``TypeError`` when the logging framework processes them.  This method
        converts known safe forms and drops everything else so logging never
        crashes due to malformed ``exc_info`` values.
        """

        exc = kwargs.pop("exc_info", None)
        if isinstance(exc, BaseException):
            # Convert bare exception objects to the tuple form expected by the
            # standard logging machinery so the traceback is preserved.
            exc = (exc.__class__, exc, exc.__traceback__)
        elif exc is True:
            # ``True`` means "use the current exception"; normalize to a tuple
            # to keep behaviour consistent with our exception-object handling.
            exc = sys.exc_info()
        elif exc not in (None, False):
            # Guard against unsupported ``exc_info`` types (e.g. strings or
            # improperly formed tuples) which would otherwise raise exceptions
            # when the base logger tries to format the record.
            if not (isinstance(exc, tuple) and len(exc) == 3):
                exc = None

        super()._log(level, msg, *args, exc_info=exc, **kwargs)


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


def log_consensus_failure(
    logger: DevSynthLogger,
    error: Exception,
    extra: Dict[str, Any] | None = None,
) -> None:
    """Log a consensus failure using ``logger``.

    The log record captures both the string representation of ``error`` and its
    class name under ``error_type`` so downstream consumers can easily
    differentiate failure categories.

    Args:
        logger: Logger instance to emit the log.
        error: The exception that triggered the failure.
        extra: Optional additional context for the log record.
    """
    data: Dict[str, Any] = {
        "error": str(error),
        "error_type": error.__class__.__name__,
    }
    if extra:
        data.update(extra)
    # Include the original exception so that stack traces are preserved.
    logger.error("Consensus failure", exc_info=error, extra=data)


__all__ = [
    "configure_logging",
    "get_logger",
    "setup_logging",
    "log_consensus_failure",
    "DevSynthLogger",
    "set_request_context",
    "clear_request_context",
]
