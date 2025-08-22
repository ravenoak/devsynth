"""Storage adapter protocol for memory backends.

This protocol defines the minimal interface required for storage backends used
by :class:`~devsynth.application.memory.memory_manager.MemoryManager`.  Each
backend exposes its ``backend_type`` for configuration-based selection and
implements the :class:`~devsynth.domain.interfaces.memory.MemoryStore` contract.
"""

from __future__ import annotations

from typing import ClassVar, Protocol

from ....domain.interfaces.memory import MemoryStore


class StorageAdapter(MemoryStore, Protocol):
    """Protocol implemented by memory storage adapters.

    Adapters expose a class-level :attr:`backend_type` used by
    :class:`~devsynth.application.memory.memory_manager.MemoryManager` to select
    the appropriate backend at runtime.
    """

    backend_type: ClassVar[str]
