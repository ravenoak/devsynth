"""Typed helpers for serializing memory metadata and query row payloads."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import cast

from .dto import (
    MemoryMetadata,
    MemoryMetadataValue,
    MemoryQueryResults,
    MemoryRecord,
    build_memory_record,
)

JSONPrimitive = str | int | float | bool | None
JSONValue = JSONPrimitive | list["JSONValue"] | dict[str, "JSONValue"]

__all__ = [
    "JSONPrimitive",
    "JSONValue",
    "dumps",
    "from_serializable",
    "loads",
    "query_results_from_rows",
    "record_from_row",
    "row_from_record",
    "to_serializable",
]


def _coerce_serialized_mapping(payload: object) -> Mapping[str, object] | None:
    if payload is None:
        return None
    if isinstance(payload, Mapping):
        return cast(Mapping[str, object], payload)
    if isinstance(payload, (bytes, bytearray)):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:  # pragma: no cover - defensive guard
            return None
    if isinstance(payload, str):
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if isinstance(decoded, Mapping):
            return cast(Mapping[str, object], decoded)
        return None
    return None


def _coerce_similarity(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _coerce_source(value: object, default: str | None = None) -> str | None:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _encode_value(value: MemoryMetadataValue) -> JSONValue:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="ignore")
    if isinstance(value, Mapping):
        return {key: _encode_value(inner) for key, inner in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_encode_value(inner) for inner in value]
    return cast(JSONPrimitive, value)


def _decode_value(value: JSONValue) -> MemoryMetadataValue:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(value, list):
        return [_decode_value(inner) for inner in value]
    if isinstance(value, dict):
        return {key: _decode_value(inner) for key, inner in value.items()}
    return value


def to_serializable(metadata: MemoryMetadata | None) -> dict[str, JSONValue]:
    if not metadata:
        return {}
    return {key: _encode_value(value) for key, value in dict(metadata).items()}


def from_serializable(payload: Mapping[str, object] | None) -> MemoryMetadata:
    result: dict[str, MemoryMetadataValue] = {}
    if not payload:
        return {}
    for key, value in payload.items():
        result[key] = _decode_value(cast(JSONValue, value))
    return result


def dumps(metadata: MemoryMetadata | None) -> str:
    return json.dumps(to_serializable(metadata))


def loads(serialized: str | bytes | bytearray | None) -> MemoryMetadata:
    if not serialized:
        return {}
    if isinstance(serialized, (bytes, bytearray)):
        payload = json.loads(serialized.decode("utf-8"))
    else:
        payload = json.loads(serialized)
    if not isinstance(payload, dict):  # pragma: no cover - defensive guard
        raise TypeError("Metadata payload must deserialize into a mapping")
    return from_serializable(payload)


def record_from_row(
    row: Mapping[str, object] | MemoryRecord,
    *,
    metadata_field: str = "metadata",
    similarity_field: str = "similarity",
    source_field: str = "source",
    default_source: str | None = None,
) -> MemoryRecord:
    """Build a :class:`MemoryRecord` from a serialized row payload.

    Parameters
    ----------
    row:
        Raw row payload returned from a persistence layer.  The helper accepts
        mappings (for example ``sqlite3.Row`` instances) or already constructed
        :class:`MemoryRecord` objects.
    metadata_field:
        Mapping key that stores serialized metadata values.  When present the
        payload is decoded via :func:`from_serializable` before being delegated
        to :func:`build_memory_record`.
    similarity_field:
        Mapping key containing similarity or score information.  The value is
        coerced into a ``float`` when possible.
    source_field:
        Mapping key that identifies the originating store.  When absent the
        ``default_source`` is used instead.
    default_source:
        Fallback store identifier applied when the row omits ``source_field``.
    """

    if isinstance(row, MemoryRecord):
        resolved_source = row.source if row.source is not None else default_source
        return build_memory_record(row, source=resolved_source)

    payload = dict(row)

    metadata_payload = payload.get(metadata_field)
    decoded_metadata = _coerce_serialized_mapping(metadata_payload)
    if decoded_metadata is not None:
        payload[metadata_field] = from_serializable(decoded_metadata)

    similarity_value = payload.pop(similarity_field, None)
    similarity = _coerce_similarity(similarity_value)

    source_value = payload.pop(source_field, None)
    source = _coerce_source(source_value, default_source)

    return build_memory_record(payload, source=source, similarity=similarity)


def row_from_record(
    record: MemoryRecord,
    *,
    metadata_field: str = "metadata",
    similarity_field: str = "similarity",
    source_field: str = "source",
    include_similarity: bool = True,
    include_source: bool = True,
) -> dict[str, object]:
    """Serialize a :class:`MemoryRecord` into a persistence-friendly mapping."""

    base_row = record.item.to_dict()
    row: dict[str, object] = dict(base_row)
    row[metadata_field] = to_serializable(record.item.metadata)

    if include_similarity and record.similarity is not None:
        row[similarity_field] = record.similarity

    if include_source and record.source:
        row[source_field] = record.source

    return row


def query_results_from_rows(
    store: str,
    rows: Iterable[Mapping[str, object] | MemoryRecord] | None,
    *,
    total: int | None = None,
    latency_ms: float | int | str | None = None,
    metadata: Mapping[str, object] | str | bytes | bytearray | None = None,
    metadata_field: str = "metadata",
    similarity_field: str = "similarity",
    source_field: str = "source",
) -> MemoryQueryResults:
    """Shape raw row payloads into :class:`MemoryQueryResults` mappings."""

    record_payloads: Iterable[Mapping[str, object] | MemoryRecord] = rows or ()
    records = [
        record_from_row(
            payload,
            metadata_field=metadata_field,
            similarity_field=similarity_field,
            source_field=source_field,
            default_source=store,
        )
        for payload in record_payloads
    ]

    result: MemoryQueryResults = {"store": store, "records": records}

    if total is not None:
        result["total"] = int(total)

    if latency_ms is not None:
        result["latency_ms"] = float(latency_ms)

    if metadata is not None:
        decoded = _coerce_serialized_mapping(metadata)
        if decoded is None and isinstance(metadata, Mapping):
            decoded = metadata
        if decoded is not None:
            normalized = from_serializable(decoded)
            if normalized:
                result["metadata"] = normalized

    return result
