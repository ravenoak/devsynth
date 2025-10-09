"""Unit coverage for metadata serialization row helpers."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from devsynth.application.memory.dto import build_memory_record
from devsynth.application.memory.metadata_serialization import (
    query_results_from_rows,
    record_from_row,
    row_from_record,
    to_serializable,
)
from devsynth.domain.models.memory import MemoryType


@pytest.mark.fast
def test_record_round_trip_preserves_metadata() -> None:
    """`record_from_row` should reverse `row_from_record` outputs."""

    nested_metadata = {
        "timestamp": datetime(2024, 1, 2, 3, 4, 5),
        "nested": {
            "count": 2,
            "entries": [
                {"seen_at": datetime(2024, 1, 2, 3, 4, 5)},
                {"seen_at": datetime(2024, 1, 2, 6, 7, 8)},
            ],
        },
    }
    record = build_memory_record(
        {
            "id": "rec-1",
            "content": {"message": "hello"},
            "memory_type": "context",
            "metadata": nested_metadata,
        },
        source="vector-store",
        similarity=0.91,
    )

    row_payload = row_from_record(record)
    restored = record_from_row(row_payload, default_source="fallback-store")

    assert restored.source == "vector-store"
    assert restored.similarity == pytest.approx(0.91)
    assert restored.item.id == "rec-1"
    assert restored.memory_type is MemoryType.CONTEXT
    assert restored.item.metadata["timestamp"] == nested_metadata["timestamp"]
    assert (
        restored.item.metadata["nested"]["entries"][0]["seen_at"]
        == nested_metadata["nested"]["entries"][0]["seen_at"]
    )


@pytest.mark.fast
def test_record_from_row_handles_stringified_metadata() -> None:
    """Metadata stored as JSON strings should be decoded automatically."""

    serialized_metadata = json.dumps(
        to_serializable(
            {
                "level": 3,
                "expires_at": datetime(2024, 5, 6, 7, 8, 9),
            }
        )
    )

    restored = record_from_row(
        {
            "id": "row-1",
            "content": "payload",
            "memory_type": "context",
            "metadata": serialized_metadata,
            "similarity": "0.42",
        },
        default_source="duckdb",
    )

    assert restored.source == "duckdb"
    assert restored.similarity == pytest.approx(0.42)
    assert restored.memory_type is MemoryType.CONTEXT
    assert restored.item.metadata["level"] == 3
    assert restored.item.metadata["expires_at"] == datetime(2024, 5, 6, 7, 8, 9)


@pytest.mark.fast
def test_query_results_from_rows_shapes_records() -> None:
    """Row helpers should produce query results with normalized metadata."""

    rows = [
        {
            "id": "a",
            "content": "alpha",
            "memory_type": "context",
            "metadata": to_serializable({"score": 1}),
        },
        {
            "id": "b",
            "content": "beta",
            "memory_type": "knowledge",
            "metadata": to_serializable({"score": 2}),
            "source": "secondary",
            "similarity": 0.33,
        },
    ]

    results = query_results_from_rows(
        "primary",
        rows,
        total="2",
        latency_ms="3.5",
        metadata=to_serializable(
            {"batch": 1, "started_at": datetime(2024, 4, 5, 6, 7)}
        ),
    )

    assert results["store"] == "primary"
    assert results["total"] == 2
    assert results["latency_ms"] == pytest.approx(3.5)
    assert results["metadata"]["batch"] == 1
    assert results["metadata"]["started_at"] == datetime(2024, 4, 5, 6, 7)

    primary_record, secondary_record = results["records"]
    assert primary_record.source == "primary"
    assert primary_record.memory_type is MemoryType.CONTEXT
    assert secondary_record.source == "secondary"
    assert secondary_record.similarity == pytest.approx(0.33)
    assert secondary_record.memory_type is MemoryType.CONTEXT


@pytest.mark.fast
def test_build_memory_record_coerces_legacy_mapping() -> None:
    """Legacy mapping payloads should coerce into typed ``MemoryRecord`` values."""

    record = build_memory_record(
        {
            "id": "legacy-1",
            "content": {"message": "hello"},
            "memory_type": "knowledge",
            "metadata": {"level": "3"},
            "score": "0.75",
            "source": "legacy-store",
        }
    )

    assert record.item.id == "legacy-1"
    assert record.memory_type is MemoryType.KNOWLEDGE
    assert record.similarity == pytest.approx(0.75)
    assert record.source == "legacy-store"
    assert record.metadata is not None
    assert record.metadata["level"] == "3"
