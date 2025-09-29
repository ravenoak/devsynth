"""Typed data transfer objects for exchanging memory records across adapters.

The DTOs in this module bridge domain-level memory models with infrastructure
layers.  They should be used when memory content leaves a store boundary (for
example, search results returned to orchestration code or aggregated results
from multiple adapters).  Direct store mutations can continue to operate on the
:class:`~devsynth.domain.models.memory.MemoryItem` dataclass, but once data is
emitted for cross-store coordination the types below provide the expected
structure and metadata normalization semantics.

``MemoryMetadata`` values should already be normalized to JSON-serializable
primitives, optional timestamps, or further mappings/lists composed of those
values.  Callers are encouraged to convert bespoke objects (for example,
``UUID`` or ``Enum`` instances) into primitive representations before exposing
them through these DTOs so downstream serialization remains predictable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import MutableMapping, Sequence, TypedDict, TypeAlias

from typing_extensions import NotRequired

MemoryMetadataValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | datetime
    | Sequence["MemoryMetadataValue"]
    | MutableMapping[str, "MemoryMetadataValue"]
)
"""Supported value types for metadata attached to memory artefacts.

The alias intentionally mirrors common JSON-serializable primitives, while also
allowing nested ``Sequence`` and ``MutableMapping`` containers composed of other
``MemoryMetadataValue`` entries.  ``datetime`` objects are permitted so callers
can attach precise timestamps prior to serialization.
"""

MemoryMetadata: TypeAlias = MutableMapping[str, MemoryMetadataValue]
"""Normalized metadata mapping carried alongside memory artefacts."""


@dataclass(slots=True)
class MemoryRecord:
    """Normalized memory record returned from store-agnostic search APIs.

    ``MemoryRecord`` packages a :class:`MemoryItem` with additional retrieval
    metadata such as similarity scores or the originating store name.  Use this
    type when returning structured results from hybrid search or aggregation
    layers.  Individual stores may continue to emit ``MemoryItem`` instances
    directly when no enrichment is required.
    """

    item: "MemoryItem"
    similarity: float | None = None
    source: str | None = None
    metadata: MemoryMetadata | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}
        else:
            # Copy into a mutable dictionary so downstream callers can safely
            # update the metadata payload without mutating shared structures.
            self.metadata = dict(self.metadata)


class MemoryQueryResults(TypedDict, total=False):
    """Results returned by querying a single memory store.

    The ``store`` field identifies the adapter emitting the results.  ``records``
    should contain normalized ``MemoryRecord`` entries.  ``total`` and
    ``latency_ms`` remain optional so adapters can share their own accounting or
    performance measurements.
    """

    store: str
    records: list[MemoryRecord]
    total: NotRequired[int]
    latency_ms: NotRequired[float]
    metadata: NotRequired[MemoryMetadata]


class GroupedMemoryResults(TypedDict, total=False):
    """Aggregated search response combining multiple :class:`MemoryQueryResults`.

    ``by_store`` holds the per-adapter results keyed by store name.  ``combined``
    may be supplied when the orchestrator merges all records into a single ranked
    list.
    """

    by_store: dict[str, MemoryQueryResults]
    combined: NotRequired[list[MemoryRecord]]
    query: NotRequired[str]
    metadata: NotRequired[MemoryMetadata]


# Delayed import to avoid circular dependencies during runtime initialization.
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from devsynth.domain.models.memory import MemoryItem

