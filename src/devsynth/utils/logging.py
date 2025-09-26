from __future__ import annotations

import sys
from types import TracebackType
from typing import Any

from devsynth.logger import configure_logging, log_consensus_failure  # re-export
from devsynth.logging_setup import DevSynthLogger as _BaseLogger

ExcInfoTuple = tuple[
    type[BaseException] | None,
    BaseException | None,
    TracebackType | None,
]
ExcInfoArg = BaseException | ExcInfoTuple | bool | None


class DevSynthLogger(_BaseLogger):
    """Project-level logger that normalizes ``exc_info`` values."""

    def _log(
        self,
        level: int,
        msg: str,
        *args: object,
        exc_info: ExcInfoArg = None,
        **kwargs: Any,
    ) -> None:
        normalized_exc: ExcInfoTuple | None
        if isinstance(exc_info, BaseException):
            normalized_exc = (
                exc_info.__class__,
                exc_info,
                exc_info.__traceback__,
            )
        elif exc_info is True:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            normalized_exc = (exc_type, exc_value, exc_traceback)
        elif exc_info in (None, False):
            normalized_exc = None
        elif isinstance(exc_info, tuple) and len(exc_info) == 3:
            normalized_exc = (
                exc_info[0],
                exc_info[1],
                exc_info[2],
            )
        else:
            normalized_exc = None

        super()._log(level, msg, *args, exc_info=normalized_exc, **kwargs)


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
