from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, TypedDict, cast

from typing_extensions import Self

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from devsynth.application.memory.dto import MemoryMetadata
else:  # Fallback to keep runtime import graph minimal.
    from typing import Mapping

    MemoryMetadata = Mapping[str, Any]


class MemoryType(Enum):
    """Types of memory in the DevSynth system."""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"
    WORKING_MEMORY = "working"  # Alias for WORKING for backward compatibility
    EPISODIC = "episodic"
    SOLUTION = "solution"
    DIALECTICAL_REASONING = "dialectical_reasoning"
    TEAM_STATE = "team_state"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    RELATIONSHIP = "relationship"
    CODE_ANALYSIS = "code_analysis"
    CODE = "code"
    CODE_TRANSFORMATION = "code_transformation"
    DOCUMENTATION = "documentation"
    CONTEXT = "context"
    CONVERSATION = "conversation"
    TASK_HISTORY = "task_history"
    KNOWLEDGE = "knowledge"
    ERROR_LOG = "error_log"
    # Collaboration-specific memory types
    COLLABORATION_TASK = "collaboration_task"
    COLLABORATION_MESSAGE = "collaboration_message"
    COLLABORATION_TEAM = "collaboration_team"
    PEER_REVIEW = "peer_review"
    EXPAND_RESULTS = "expand_results"
    DIFFERENTIATE_RESULTS = "differentiate_results"
    REFINE_RESULTS = "refine_results"
    RETROSPECT_RESULTS = "retrospect_results"
    FINAL_REPORT = "final_report"
    EDRR_CYCLE_RESULTS = "edrr_cycle_results"
    INGEST_EXPAND_RESULTS = "ingest_expand_results"
    INGEST_DIFFERENTIATE_RESULTS = "ingest_differentiate_results"
    INGEST_REFINE_RESULTS = "ingest_refine_results"
    INGEST_RETROSPECT_RESULTS = "ingest_retrospect_results"

    @classmethod
    def from_raw(cls, raw: object) -> "MemoryType":
        """Coerce arbitrary representations into a :class:`MemoryType`.

        Historically adapters accepted either an enum instance, its value, or an
        uppercase string matching the enum name.  This helper normalizes those
        representations so storage layers consistently operate on
        :class:`MemoryType` values while remaining tolerant of existing data.
        """

        if isinstance(raw, cls):
            return raw

        try:
            return cls(raw)
        except ValueError as error:
            if isinstance(raw, str):
                try:
                    return cls[raw]
                except KeyError as exc:  # pragma: no cover - defensive
                    raise ValueError(f"Unknown memory type: {raw!r}") from exc
            raise ValueError(f"Unknown memory type: {raw!r}") from error


# Alias for backward compatibility and for use in tests
MemoryItemType = MemoryType


@dataclass
class MemoryItem:
    """A single item stored in memory."""

    id: str
    content: Any
    memory_type: MemoryType
    metadata: MemoryMetadata | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        self.memory_type = MemoryType.from_raw(self.memory_type)
        if self.metadata is None:
            self.metadata = cast(MemoryMetadata, {})
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> "SerializedMemoryItem":
        """Return a serialized representation suitable for adapters.

        Metadata mappings are copied to prevent downstream mutation from
        affecting the stored ``MemoryItem`` instance.
        """

        metadata = None
        if self.metadata is not None:
            metadata = cast(MemoryMetadata, dict(self.metadata))

        created_at = self.created_at.isoformat() if self.created_at else None
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "metadata": metadata,
            "created_at": created_at,
        }

    @classmethod
    def from_dict(cls, payload: "SerializedMemoryItem") -> Self:
        """Reconstruct a :class:`MemoryItem` from serialized data."""

        metadata = payload.get("metadata")
        normalized_metadata = None
        if metadata is not None:
            normalized_metadata = cast(MemoryMetadata, dict(metadata))

        created_at = payload.get("created_at")
        parsed_created_at = None
        if created_at:
            try:
                parsed_created_at = datetime.fromisoformat(created_at)
            except ValueError:  # pragma: no cover - defensive parsing guard
                logger.warning("Invalid created_at value %s", created_at)

        return cls(
            id=payload["id"],
            content=payload["content"],
            memory_type=MemoryType.from_raw(payload["memory_type"]),
            metadata=normalized_metadata,
            created_at=parsed_created_at,
        )


@dataclass
class MemoryVector:
    """A vector representation of a memory item."""

    id: str
    content: Any
    embedding: list[float]
    metadata: MemoryMetadata | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = cast(MemoryMetadata, {})
        if self.created_at is None:
            self.created_at = datetime.now()


class SerializedMemoryItem(TypedDict):
    """Typed representation of a serialized :class:`MemoryItem`."""

    id: str
    content: Any
    memory_type: str
    metadata: MemoryMetadata | None
    created_at: str | None
