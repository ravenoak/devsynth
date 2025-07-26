"""
Memory module for DevSynth.

This module provides memory storage and retrieval functionality for DevSynth,
including a Memory Manager with adapters for different storage backends.
"""

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from .context_manager import InMemoryStore, SimpleContextManager
from .json_file_store import JSONFileStore
from .memory_manager import MemoryManager
from .search_patterns import SearchPatterns
from .persistent_context_manager import PersistentContextManager
from .multi_layered_memory import MultiLayeredMemorySystem

logger = DevSynthLogger(__name__)

from devsynth.exceptions import DevSynthError

try:  # pragma: no cover - optional dependency
    from .adapters.graph_memory_adapter import GraphMemoryAdapter
except ImportError as exc:  # pragma: no cover - fallback path
    GraphMemoryAdapter = None
    logger.warning("GraphMemoryAdapter not available: %s", exc)

try:  # pragma: no cover - optional dependency
    from .adapters.vector_memory_adapter import VectorMemoryAdapter
except ImportError as exc:  # pragma: no cover - fallback path
    VectorMemoryAdapter = None
    logger.warning("VectorMemoryAdapter not available: %s", exc)

try:  # pragma: no cover - optional dependency
    from .adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
except ImportError as exc:  # pragma: no cover - fallback path
    TinyDBMemoryAdapter = None
    logger.warning("TinyDBMemoryAdapter not available: %s", exc)

__all__ = [
    "InMemoryStore",
    "SimpleContextManager",
    "JSONFileStore",
    "PersistentContextManager",
    "MemoryManager",
    "SearchPatterns",
    "MultiLayeredMemorySystem",
]

if GraphMemoryAdapter is not None:
    __all__.append("GraphMemoryAdapter")

if VectorMemoryAdapter is not None:
    __all__.append("VectorMemoryAdapter")

if TinyDBMemoryAdapter is not None:
    __all__.append("TinyDBMemoryAdapter")
