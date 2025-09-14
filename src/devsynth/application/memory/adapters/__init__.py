"""Memory Adapters Package

This package provides adapters for different memory storage backends.
"""

from devsynth.logging_setup import DevSynthLogger

from .graph_memory_adapter import GraphMemoryAdapter
from .storage_adapter import StorageAdapter
from .tinydb_memory_adapter import TinyDBMemoryAdapter
from .vector_memory_adapter import VectorMemoryAdapter

logger = DevSynthLogger(__name__)

KuzuAdapter: type[StorageAdapter] | None
try:  # pragma: no cover - optional dependency
    from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter as _KuzuAdapter

    KuzuAdapter = _KuzuAdapter
except Exception as exc:  # pragma: no cover - missing optional dependency
    KuzuAdapter = None
    logger.warning("KuzuAdapter not available: %s", exc)

S3MemoryAdapter: type[StorageAdapter] | None
try:  # pragma: no cover - optional dependency
    from .s3_memory_adapter import S3MemoryAdapter as _S3MemoryAdapter

    S3MemoryAdapter = _S3MemoryAdapter
except Exception as exc:  # pragma: no cover - missing optional dependency
    S3MemoryAdapter = None
    logger.warning("S3MemoryAdapter not available: %s", exc)

__all__ = [
    "GraphMemoryAdapter",
    "VectorMemoryAdapter",
    "TinyDBMemoryAdapter",
    "StorageAdapter",
]

if KuzuAdapter is not None:
    __all__.append("KuzuAdapter")
if S3MemoryAdapter is not None:
    __all__.append("S3MemoryAdapter")
