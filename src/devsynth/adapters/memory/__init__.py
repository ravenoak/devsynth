"""Memory adapter package for abstracting persistence layers."""

from typing import Any

from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

MultiStoreSyncManager: type[Any] | None
try:  # pragma: no cover - optional dependency
    from .sync_manager import MultiStoreSyncManager
except Exception as exc:  # pragma: no cover - graceful fallback
    logger.debug("Sync manager unavailable: %s", exc)
    MultiStoreSyncManager = None

__all__ = ["MultiStoreSyncManager"]
