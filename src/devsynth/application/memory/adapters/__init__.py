"""Memory Adapters Package

This package provides adapters for different memory storage backends.
"""

from typing import TYPE_CHECKING, cast

from devsynth.logging_setup import DevSynthLogger

from ..dto import MemorySearchQuery, VectorStoreStats
from .graph_memory_adapter import GraphMemoryAdapter
from .storage_adapter import StorageAdapter
from .tinydb_memory_adapter import TinyDBMemoryAdapter
from .vector_memory_adapter import VectorMemoryAdapter

logger = DevSynthLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - imported for static analysis only
    from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter as KuzuAdapterType

    from .s3_memory_adapter import S3MemoryAdapter as S3MemoryAdapterType
else:  # pragma: no cover - runtime fallback when optional adapters missing
    KuzuAdapterType = StorageAdapter  # type: ignore[assignment]
    S3MemoryAdapterType = StorageAdapter  # type: ignore[assignment]

KuzuAdapter: type[KuzuAdapterType] | None
try:  # pragma: no cover - optional dependency
    from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter as _KuzuAdapter
except Exception as exc:  # pragma: no cover - missing optional dependency
    KuzuAdapter = None
    logger.warning("KuzuAdapter not available: %s", exc)
else:
    KuzuAdapter = cast("type[KuzuAdapterType]", _KuzuAdapter)

S3MemoryAdapter: type[S3MemoryAdapterType] | None
try:  # pragma: no cover - optional dependency
    from .s3_memory_adapter import S3MemoryAdapter as _S3MemoryAdapter
except Exception as exc:  # pragma: no cover - missing optional dependency
    S3MemoryAdapter = None
    logger.warning("S3MemoryAdapter not available: %s", exc)
else:
    S3MemoryAdapter = cast("type[S3MemoryAdapterType]", _S3MemoryAdapter)

__all__ = [
    "GraphMemoryAdapter",
    "VectorMemoryAdapter",
    "TinyDBMemoryAdapter",
    "StorageAdapter",
    "MemorySearchQuery",
    "VectorStoreStats",
]

if KuzuAdapter is not None:
    __all__.append("KuzuAdapter")
if S3MemoryAdapter is not None:
    __all__.append("S3MemoryAdapter")
