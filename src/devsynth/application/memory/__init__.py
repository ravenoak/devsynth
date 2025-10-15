from __future__ import annotations

"""
Memory module for DevSynth.

This module provides memory storage and retrieval functionality for DevSynth,
including a Memory Manager with adapters for different storage backends.
"""

from typing import TYPE_CHECKING, Any, ClassVar, cast

from devsynth.logging_setup import DevSynthLogger

from .context_manager import InMemoryStore, SimpleContextManager
from .json_file_store import JSONFileStore
from .memory_manager import MemoryManager
from .multi_layered_memory import MultiLayeredMemorySystem
from .persistent_context_manager import PersistentContextManager
from .search_patterns import SearchPatterns
from .vector_providers import factory as vector_store_factory

logger = DevSynthLogger(__name__)

from devsynth.exceptions import DevSynthError

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from .adapters.graph_memory_adapter import (
        GraphMemoryAdapter as GraphMemoryAdapterType,
    )
    from .adapters.tinydb_memory_adapter import (
        TinyDBMemoryAdapter as TinyDBMemoryAdapterType,
    )
    from .adapters.vector_memory_adapter import (
        VectorMemoryAdapter as VectorMemoryAdapterType,
    )
else:  # pragma: no cover - fallback definitions when optional adapters missing
    GraphMemoryAdapterType = Any  # type: ignore[assignment]
    TinyDBMemoryAdapterType = Any  # type: ignore[assignment]
    VectorMemoryAdapterType = Any  # type: ignore[assignment]

GraphMemoryAdapter: ClassVar[type[GraphMemoryAdapterType] | None]
try:  # pragma: no cover - optional dependency
    from .adapters.graph_memory_adapter import GraphMemoryAdapter as _GraphMemoryAdapter
except ImportError as exc:  # pragma: no cover - fallback path
    GraphMemoryAdapter = None
    logger.warning("GraphMemoryAdapter not available: %s", exc)
else:
    GraphMemoryAdapter = cast("type[GraphMemoryAdapterType]", _GraphMemoryAdapter)

VectorMemoryAdapter: ClassVar[type[VectorMemoryAdapterType] | None]
try:  # pragma: no cover - optional dependency
    from .adapters.vector_memory_adapter import (
        VectorMemoryAdapter as _VectorMemoryAdapter,
    )
except ImportError as exc:  # pragma: no cover - fallback path
    VectorMemoryAdapter = None
    logger.warning("VectorMemoryAdapter not available: %s", exc)
else:
    VectorMemoryAdapter = cast("type[VectorMemoryAdapterType]", _VectorMemoryAdapter)

TinyDBMemoryAdapter: ClassVar[type[TinyDBMemoryAdapterType] | None]
try:  # pragma: no cover - optional dependency
    from .adapters.tinydb_memory_adapter import (
        TinyDBMemoryAdapter as _TinyDBMemoryAdapter,
    )
except ImportError as exc:  # pragma: no cover - fallback path
    TinyDBMemoryAdapter = None
    logger.warning("TinyDBMemoryAdapter not available: %s", exc)
else:
    TinyDBMemoryAdapter = cast("type[TinyDBMemoryAdapterType]", _TinyDBMemoryAdapter)

__all__: list[str] = [
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

__all__.append("vector_store_factory")
