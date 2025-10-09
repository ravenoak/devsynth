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

from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, TypeAlias, TypedDict, cast

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

MemoryMetadata: TypeAlias = Mapping[str, MemoryMetadataValue]
"""Normalized metadata mapping carried alongside memory artefacts."""


MemoryQueryValue: TypeAlias = (
    MemoryMetadataValue
    | Sequence[MemoryMetadataValue]
    | Mapping[str, MemoryMetadataValue]
)
"""Supported value types accepted by structured memory search queries."""

MemorySearchQuery: TypeAlias = Mapping[str, MemoryQueryValue]
"""Normalized query mapping accepted by memory search adapters."""


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

        return self.item.id

    @property
    def content(self) -> MemoryMetadataValue:
        """Return the wrapped item's content using metadata-compatible types."""

        return cast(MemoryMetadataValue, self.item.content)

    @property
    def memory_type(self) -> MemoryType:
        """Return the wrapped item's memory type."""

        return self.item.memory_type

    @property
    def created_at(self) -> datetime | None:
        """Mirror the wrapped item's ``created_at`` timestamp."""

        return self.item.created_at

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


class VectorStoreStats(TypedDict, total=False):
    """Normalized statistics returned by vector-backed adapters."""

    vector_count: int
    embedding_dimensions: NotRequired[int]
    collection_name: NotRequired[str]
    persist_directory: NotRequired[str | None]
    metadata: NotRequired[MemoryMetadata]


# Delayed import to avoid circular dependencies during runtime initialization.
if TYPE_CHECKING:  # pragma: no cover - type checking only
    from devsynth.domain.models.memory import MemoryVector

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

LegacyRecordMapping: TypeAlias = Mapping[str, object]
LegacyRecordTuple: TypeAlias = tuple[
    MemoryRecord | MemoryItem | MemoryVector | LegacyRecordMapping,
    float | int | None,
]

MemoryRecordInput: TypeAlias = (
    MemoryRecord
    | MemoryItem
    | MemoryVector
    | LegacyRecordMapping
    | LegacyRecordTuple
    | None
)


def _normalize_metadata(*payloads: MemoryMetadata | None) -> MemoryMetadata | None:
    merged: dict[str, MemoryMetadataValue] = {}
    for payload in payloads:
        if not payload:
            continue
        merged.update(dict(payload))
    return merged if merged else None


def _coerce_metadata_value(value: object) -> MemoryMetadataValue:
    """Normalize arbitrary payloads into ``MemoryMetadataValue`` instances."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, datetime):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _coerce_metadata_value(inner_value)
            for key, inner_value in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_coerce_metadata_value(inner) for inner in value]
    return str(value)


def _coerce_metadata(payload: object) -> MemoryMetadata | None:
    if not isinstance(payload, Mapping):
        return None
    normalized: dict[str, MemoryMetadataValue] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            normalized[str(key)] = _coerce_metadata_value(value)
        else:
            normalized[key] = _coerce_metadata_value(value)
    return normalized


def _coerce_created_at(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:  # pragma: no cover - defensive guard
            return None
    return None


def _coerce_similarity(*values: object) -> float | None:
    for candidate in values:
        if isinstance(candidate, (int, float)):
            return float(candidate)
        if isinstance(candidate, str):
            try:
                return float(candidate)
            except ValueError:  # pragma: no cover - defensive guard
                continue
    return None


def _coerce_memory_type(
    value: object, fallback: MemoryType = MemoryType.CONTEXT
) -> MemoryType:
    try:
        return MemoryType.from_raw(value)
    except ValueError:
        return fallback


def _memory_item_from_vector(vector: MemoryVector) -> MemoryItem:
    vector_metadata = {
        key: _coerce_metadata_value(value)
        for key, value in (vector.metadata or {}).items()
    }
    raw_type = vector_metadata.get("memory_type")
    memory_type = (
        _coerce_memory_type(raw_type) if raw_type is not None else MemoryType.CONTEXT
    )
    vector_metadata["memory_type"] = memory_type.value
    vector_metadata.setdefault("embedding", list(vector.embedding))
    return MemoryItem(
        id=vector.id,
        content=vector.content,
        memory_type=memory_type,
        metadata=vector_metadata,
        created_at=vector.created_at,
    )


def _memory_item_from_mapping(
    payload: LegacyRecordMapping,
) -> tuple[MemoryItem, MemoryMetadata | None]:
    if "item" in payload and isinstance(payload["item"], MemoryItem):
        item = payload["item"]
        return item, item.metadata

    raw_type = payload.get("memory_type", MemoryType.CONTEXT)
    memory_type = _coerce_memory_type(raw_type)
    metadata_payload = _coerce_metadata(payload.get("metadata"))
    created_at = _coerce_created_at(payload.get("created_at"))
    item = MemoryItem(
        id=str(payload.get("id", "")),
        content=payload.get("content"),
        memory_type=memory_type,
        metadata=metadata_payload,
        created_at=created_at,
    )
    return item, metadata_payload


def build_memory_record(
    payload: MemoryRecordInput,
    *,
    source: str | None = None,
    similarity: float | None = None,
    metadata: MemoryMetadata | None = None,
) -> MemoryRecord:
    """Coerce adapter payloads into :class:`MemoryRecord` instances."""

    record_source = source

    if payload is None:
        item = MemoryItem(id="", content="", memory_type=MemoryType.CONTEXT)
        base_similarity = None
        base_metadata: MemoryMetadata | None = None
    elif isinstance(payload, MemoryRecord):
        base_similarity = payload.similarity
        base_metadata = payload.metadata
        item = payload.item
        if record_source is None:
            record_source = payload.source
    else:
        tuple_similarity: float | None = None
        underlying: object = payload
        if isinstance(payload, tuple) and len(payload) == 2:
            candidate, candidate_score = payload
            tuple_similarity = _coerce_similarity(candidate_score)
            underlying = candidate
        base_metadata = None
        if isinstance(underlying, MemoryItem):
            item = underlying
            base_metadata = underlying.metadata
        elif isinstance(underlying, MemoryVector):
            item = _memory_item_from_vector(underlying)
            base_metadata = item.metadata
        elif isinstance(underlying, Mapping):
            mapping = cast(LegacyRecordMapping, underlying)
            item, base_metadata = _memory_item_from_mapping(mapping)
            if record_source is None:
                raw_source = mapping.get("source")
                record_source = raw_source if isinstance(raw_source, str) else None
            if tuple_similarity is None:
                tuple_similarity = _coerce_similarity(
                    mapping.get("similarity"), mapping.get("score")
                )
            if base_metadata is None and "metadata" in mapping:
                base_metadata = _coerce_metadata(mapping.get("metadata"))
        else:  # pragma: no cover - defensive fallback for unexpected payloads
            item = MemoryItem(id="", content=underlying, memory_type=MemoryType.CONTEXT)
            base_metadata = item.metadata
        base_similarity = tuple_similarity

    merged_similarity = similarity if similarity is not None else base_similarity
    merged_metadata = _normalize_metadata(base_metadata, metadata)

    return MemoryRecord(
        item=item,
        similarity=merged_similarity,
        source=record_source,
        metadata=merged_metadata,
    )


def build_query_results(
    store: str,
    payload: (
        MemoryQueryResults | Sequence[MemoryRecordInput] | MemoryRecordInput | None
    ),
    *,
    metadata: MemoryMetadata | None = None,
) -> MemoryQueryResults:
    """Normalize adapter responses into a :class:`MemoryQueryResults` mapping."""

    if isinstance(payload, dict) and "records" in payload:
        store_name = payload.get("store", store)
        records_iter = payload.get("records", [])
        records = [
            build_memory_record(record, source=store_name) for record in records_iter
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
    elif isinstance(payload, Sequence) and not isinstance(
        payload, (str, bytes, bytearray)
    ):
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
        current_score = (
            current.similarity if current.similarity is not None else float("-inf")
        )
        new_score = (
            record.similarity if record.similarity is not None else float("-inf")
        )
        if new_score > current_score:
            best_by_id[identifier] = record
    return list(best_by_id.values())
