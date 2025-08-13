from __future__ import annotations

import sys

from devsynth.logger import configure_logging, log_consensus_failure  # re-export
from devsynth.logging_setup import DevSynthLogger as _BaseLogger


class DevSynthLogger(_BaseLogger):
    """Project-level logger that normalizes ``exc_info`` values."""

    def _log(self, level: int, msg: str, *args, **kwargs) -> None:  # type: ignore[override]
        exc = kwargs.pop("exc_info", None)
        if isinstance(exc, BaseException):
            exc = (exc.__class__, exc, exc.__traceback__)
        elif exc is True:
            exc = sys.exc_info()
        elif exc not in (None, False) and not (
            isinstance(exc, tuple) and len(exc) == 3
        ):
            exc = None
        super()._log(level, msg, *args, exc_info=exc, **kwargs)


def get_logger(name: str) -> DevSynthLogger:
    """Return a :class:`DevSynthLogger` for ``name``."""
    return DevSynthLogger(name)


def setup_logging(name: str, log_level: int | str | None = None) -> DevSynthLogger:
    """Configure logging and return a logger for ``name``."""
    configure_logging(log_level)
    return DevSynthLogger(name)


__all__ = [
    "DevSynthLogger",
    "get_logger",
    "setup_logging",
    "configure_logging",
    "log_consensus_failure",
]
