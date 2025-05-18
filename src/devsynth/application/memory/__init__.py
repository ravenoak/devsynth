"""
Memory module for DevSynth.
"""

from .context_manager import InMemoryStore, SimpleContextManager
from .json_file_store import JSONFileStore
from .persistent_context_manager import PersistentContextManager

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

__all__ = [
    "InMemoryStore",
    "SimpleContextManager",
    "JSONFileStore",
    "PersistentContextManager",
]
