"""Minimal helpers for displaying CLI errors."""

from __future__ import annotations

from devsynth.application.cli.models import (
    BridgeErrorDetails,
    BridgeErrorPayload,
    SupportsBridgeErrorPayload,
)
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import get_logger


def _render_bridge_error(
    error: BridgeErrorPayload,
) -> Exception | dict[str, object] | str:
    if isinstance(error, Exception) or isinstance(error, str):
        return error
    if isinstance(error, BridgeErrorDetails):
        return dict(error.to_bridge_error())
    if isinstance(error, SupportsBridgeErrorPayload):
        return dict(error.to_bridge_error())
    return str(error)


def handle_error(bridge: UXBridge, error: BridgeErrorPayload) -> None:
    """Log and delegate error display to the active bridge."""
    logger = get_logger("cli_errors")
    if isinstance(error, Exception):
        logger.error("Command error: %s", error, exc_info=True)
    else:
        logger.error("Command error: %s", error)
    bridge.handle_error(_render_bridge_error(error))


# Backwards compatibility with the previous API name
handle_error_enhanced = handle_error

__all__ = ["handle_error", "handle_error_enhanced"]
