from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


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
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        self.memory_type = MemoryType.from_raw(self.memory_type)
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class MemoryVector:
    """A vector representation of a memory item."""

    id: str
    content: Any
    embedding: list[float]
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


class SerializedMemoryItem(TypedDict):
    """Typed representation of a serialized :class:`MemoryItem`."""

    id: str
    content: Any
    memory_type: str
    metadata: dict[str, Any] | None
    created_at: str | None
