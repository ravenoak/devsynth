"""
Memory Adapters Package

This package provides adapters for different memory storage backends.
"""
from devsynth.logging_setup import DevSynthLogger

from .graph_memory_adapter import GraphMemoryAdapter
from .vector_memory_adapter import VectorMemoryAdapter
from .tinydb_memory_adapter import TinyDBMemoryAdapter

logger = DevSynthLogger(__name__)

try:  # pragma: no cover - optional dependency
    from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter
except Exception as exc:  # pragma: no cover - missing optional dependency
    KuzuAdapter = None
    logger.warning("KuzuAdapter not available: %s", exc)

__all__ = [
    'GraphMemoryAdapter',
    'VectorMemoryAdapter',
    'TinyDBMemoryAdapter',
]

if KuzuAdapter is not None:
    __all__.append('KuzuAdapter')