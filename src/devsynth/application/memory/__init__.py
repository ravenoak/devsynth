"""
Memory module for DevSynth.

This module provides memory storage and retrieval functionality for DevSynth,
including a Memory Manager with adapters for different storage backends.
"""

from .context_manager import InMemoryStore, SimpleContextManager
from .json_file_store import JSONFileStore
from .persistent_context_manager import PersistentContextManager
from .memory_manager import MemoryManager
from .adapters import GraphMemoryAdapter, VectorMemoryAdapter, TinyDBMemoryAdapter

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

__all__ = [
    "InMemoryStore",
    "SimpleContextManager",
    "JSONFileStore",
    "PersistentContextManager",
    "MemoryManager",
    "GraphMemoryAdapter",
    "VectorMemoryAdapter",
    "TinyDBMemoryAdapter",
]
