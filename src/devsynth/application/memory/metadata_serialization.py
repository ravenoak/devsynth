"""Typed helpers for serializing and deserializing memory metadata payloads."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Mapping, Sequence, cast

from .dto import MemoryMetadata, MemoryMetadataValue

JSONPrimitive = str | int | float | bool | None
JSONValue = JSONPrimitive | list["JSONValue"] | dict[str, "JSONValue"]


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
    return {key: _encode_value(value) for key, value in metadata.items()}


def from_serializable(payload: Mapping[str, object] | None) -> MemoryMetadata:
    result: MemoryMetadata = {}
    if not payload:
        return result
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
