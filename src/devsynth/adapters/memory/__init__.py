"""Memory adapter package for abstracting persistence layers."""

from devsynth.exceptions import DevSynthError
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

from .sync_manager import MultiStoreSyncManager

__all__ = ["MultiStoreSyncManager"]
