"""Global UXBridge accessor for server components.

This module exposes helper functions to share a single
:class:`~devsynth.interface.ux_bridge.UXBridge` instance
between the CLI, WebUI and Agent API.  The default
bridge implementation is chosen based on project
configuration via :func:`devsynth.interface.uxbridge_config.get_default_bridge`.
"""

from __future__ import annotations

from typing import Optional

from devsynth.interface.ux_bridge import UXBridge
from devsynth.interface.uxbridge_config import get_default_bridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

_bridge: UXBridge | None = None


def get_bridge() -> UXBridge:
    """Return the active :class:`UXBridge` instance.

    If no bridge has been set explicitly, the default
    implementation from configuration is created lazily.
    """

    global _bridge
    if _bridge is None:
        _bridge = get_default_bridge()
        logger.debug("Initialized UXBridge %s", _bridge.__class__.__name__)
    return _bridge


def set_bridge(bridge: UXBridge) -> None:
    """Override the active :class:`UXBridge` instance."""

    global _bridge
    _bridge = bridge
    logger.debug("UXBridge overridden with %s", bridge.__class__.__name__)


__all__ = ["get_bridge", "set_bridge"]
