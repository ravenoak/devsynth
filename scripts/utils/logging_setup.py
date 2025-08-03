"""Helper utilities for configuring DevSynth logging in scripts."""

from __future__ import annotations

from devsynth.logging_setup import DevSynthLogger, configure_logging, get_logger


def setup_logging(name: str) -> DevSynthLogger:
    """Configure logging and return a :class:`DevSynthLogger` instance.

    This helper ensures scripts consistently initialize the DevSynth logging
    system before obtaining a logger.

    Args:
        name: Name to associate with the logger, typically ``__name__``.

    Returns:
        A configured :class:`DevSynthLogger` instance.
    """

    configure_logging()
    return get_logger(name)


__all__ = ["setup_logging", "DevSynthLogger"]
