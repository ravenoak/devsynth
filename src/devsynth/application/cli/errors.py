"""Minimal helpers for displaying CLI errors."""

from __future__ import annotations

from typing import Any, Dict, Union

from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import get_logger


def handle_error(
    bridge: UXBridge, error: Union[Exception, Dict[str, Any], str]
) -> None:
    """Log and delegate error display to the active bridge."""
    logger = get_logger("cli_errors")
    if isinstance(error, Exception):
        logger.error("Command error: %s", error, exc_info=True)
    else:
        logger.error("Command error: %s", error)
    bridge.handle_error(error)


# Backwards compatibility with the previous API name
handle_error_enhanced = handle_error

__all__ = ["handle_error", "handle_error_enhanced"]
