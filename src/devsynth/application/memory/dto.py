"""DTO helpers for normalizing memory search responses.

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
from typing import Iterable, MutableMapping, Sequence, TypedDict, TypeAlias, cast

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

    item: MemoryItem
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

    @property
    def id(self) -> str:
        """Expose the underlying item's identifier for backward compatibility."""

        return cast(str, self.item.id)

    @property
    def content(self) -> object:
        """Return the wrapped item's content."""

        return self.item.content

    @property
    def memory_type(self) -> object:
        """Return the wrapped item's memory type."""

        return self.item.memory_type

    @property
    def created_at(self) -> datetime | None:
        """Mirror the wrapped item's ``created_at`` timestamp."""

        return cast(datetime | None, self.item.created_at)

    @property
    def score(self) -> float | None:
        """Alias ``similarity`` for legacy callers."""

        return self.similarity


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
    from devsynth.domain.models.memory import MemoryItem, MemoryVector

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


def _normalize_metadata(*payloads: MemoryMetadata | None) -> MemoryMetadata | None:
    merged: MemoryMetadata = {}
    for payload in payloads:
        if not payload:
            continue
        merged.update(payload)
    return merged or None


def build_memory_record(
    payload: MemoryRecord | MemoryItem | MemoryVector | tuple[object, float] | None,
    *,
    source: str | None = None,
    similarity: float | None = None,
    metadata: MemoryMetadata | None = None,
) -> MemoryRecord:
    """Coerce adapter payloads into :class:`MemoryRecord` instances."""

    if payload is None:
        item = MemoryItem(id="", content="", memory_type=MemoryType.CONTEXT)
        base_similarity = None
        base_metadata: MemoryMetadata | None = None
    elif isinstance(payload, MemoryRecord):
        base_similarity = payload.similarity
        base_metadata = payload.metadata
        item = payload.item
    else:
        tuple_similarity: float | None = None
        underlying = payload
        if isinstance(payload, tuple) and len(payload) == 2:
            possible_item, possible_score = payload
            if isinstance(possible_score, (int, float)):
                underlying = possible_item
                tuple_similarity = float(possible_score)
        if isinstance(underlying, MemoryItem):
            item = underlying
        elif isinstance(underlying, MemoryVector):
            vector_metadata = dict(underlying.metadata or {})
            raw_type = vector_metadata.get("memory_type")
            try:
                memory_type = (
                    MemoryType.from_raw(raw_type)
                    if raw_type is not None
                    else MemoryType.CONTEXT
                )
            except ValueError:
                memory_type = MemoryType.CONTEXT
            vector_metadata["memory_type"] = memory_type.value
            vector_metadata.setdefault("embedding", list(underlying.embedding))
            item = MemoryItem(
                id=underlying.id,
                content=underlying.content,
                memory_type=memory_type,
                metadata=vector_metadata,
                created_at=underlying.created_at,
            )
        else:
            if hasattr(underlying, "get"):
                mapping = dict(underlying)  # type: ignore[arg-type]
                raw_type = mapping.get("memory_type", MemoryType.CONTEXT)
                try:
                    memory_type = MemoryType.from_raw(raw_type)
                except ValueError:
                    memory_type = MemoryType.CONTEXT
                item = MemoryItem(
                    id=mapping.get("id", ""),
                    content=mapping.get("content"),
                    memory_type=memory_type,
                    metadata=mapping.get("metadata"),
                )
                base_metadata = mapping.get("metadata")
            else:  # pragma: no cover - defensive fallback for unexpected payloads
                item = MemoryItem(id="", content=underlying, memory_type=MemoryType.CONTEXT)
        base_similarity = tuple_similarity
        base_metadata = getattr(item, "metadata", None)

    merged_similarity = similarity if similarity is not None else base_similarity
    merged_metadata = _normalize_metadata(base_metadata, metadata)

    record_source = source
    if record_source is None and isinstance(payload, MemoryRecord):
        record_source = payload.source

    return MemoryRecord(
        item=item,
        similarity=merged_similarity,
        source=record_source,
        metadata=merged_metadata,
    )


def build_query_results(
    store: str,
    payload: MemoryQueryResults | Sequence[object] | object | None,
    *,
    metadata: MemoryMetadata | None = None,
) -> MemoryQueryResults:
    """Normalize adapter responses into a :class:`MemoryQueryResults` mapping."""

    if isinstance(payload, dict) and "records" in payload:
        store_name = payload.get("store", store)
        records_iter = payload.get("records", [])
        records = [
            build_memory_record(record, source=store_name)
            for record in records_iter
        ]
        combined_metadata = _normalize_metadata(payload.get("metadata"), metadata)
        normalized: MemoryQueryResults = {"store": store_name, "records": records}
        if "total" in payload and payload["total"] is not None:
            normalized["total"] = int(payload["total"])
        if "latency_ms" in payload and payload["latency_ms"] is not None:
            normalized["latency_ms"] = float(payload["latency_ms"])
        if combined_metadata:
            normalized["metadata"] = combined_metadata
        return normalized

    normalized_records: list[MemoryRecord]
    if payload is None:
        normalized_records = []
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        normalized_records = [
            build_memory_record(item, source=store) for item in payload
        ]
    else:
        normalized_records = [build_memory_record(payload, source=store)]

    combined_metadata = _normalize_metadata(metadata)
    result: MemoryQueryResults = {"store": store, "records": normalized_records}
    if combined_metadata:
        result["metadata"] = combined_metadata
    return result


def deduplicate_records(records: Iterable[MemoryRecord]) -> list[MemoryRecord]:
    """Collapse duplicate records by ``MemoryItem`` identifier."""

    best_by_id: dict[str, MemoryRecord] = {}
    for record in records:
        identifier = record.item.id or f"{record.source}:{id(record.item)}"
        current = best_by_id.get(identifier)
        if current is None:
            best_by_id[identifier] = record
            continue
        current_score = current.similarity if current.similarity is not None else float("-inf")
        new_score = record.similarity if record.similarity is not None else float("-inf")
        if new_score > current_score:
            best_by_id[identifier] = record
    return list(best_by_id.values())

