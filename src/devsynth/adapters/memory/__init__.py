"""Memory adapter package for abstracting persistence layers."""

from devsynth.exceptions import DevSynthError
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

try:  # pragma: no cover - optional dependency
    from .sync_manager import MultiStoreSyncManager
except Exception as exc:  # pragma: no cover - graceful fallback
    logger.debug("Sync manager unavailable: %s", exc)
    MultiStoreSyncManager = None  # type: ignore[assignment]

__all__ = ["MultiStoreSyncManager"]
