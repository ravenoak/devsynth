from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypedDict, cast
from uuid import UUID, uuid4

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


# Memetic Unit Enums and Types

class MemeticSource(Enum):
    """Source types for memetic units."""
    USER_INPUT = "user_input"
    AGENT_SELF = "agent_self"
    LLM_RESPONSE = "llm_response"
    CODE_EXECUTION = "code_execution"
    TEST_RESULT = "test_result"
    FILE_INGESTION = "file_ingestion"
    API_RESPONSE = "api_response"
    ERROR_LOG = "error_log"
    METRIC_DATA = "metric_data"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"


class CognitiveType(Enum):
    """Cognitive function types for memory processing."""
    WORKING = "working"      # Active manipulation, current context
    EPISODIC = "episodic"    # Experience record, chronological
    SEMANTIC = "semantic"    # General knowledge, world model
    PROCEDURAL = "procedural" # Skills, plans, executable knowledge


class MemeticStatus(Enum):
    """Lifecycle status of memetic units."""
    RAW = "raw"              # Initial ingestion, unprocessed
    PROCESSED = "processed"  # Basic processing complete
    CONSOLIDATED = "consolidated" # Pattern extracted, abstracted
    ARCHIVED = "archived"    # Low relevance, compressed
    DEPRECATED = "deprecated" # Outdated, marked for removal


@dataclass
class MemeticLink:
    """Represents a relationship between memetic units."""
    target_id: UUID
    relationship_type: str
    strength: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemeticMetadata:
    """Comprehensive metadata for memetic units."""

    # Identity & Provenance
    unit_id: UUID = field(default_factory=uuid4)
    parent_id: Optional[UUID] = None  # Causal predecessor
    source: MemeticSource = MemeticSource.USER_INPUT
    timestamp_created: datetime = field(default_factory=datetime.now)
    timestamp_accessed: Optional[datetime] = None
    timestamp_modified: Optional[datetime] = None

    # Cognitive Type
    cognitive_type: CognitiveType = CognitiveType.WORKING

    # Semantic Descriptors
    content_hash: str = ""
    semantic_vector: List[float] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    topic: str = ""
    summary: str = ""

    # State & Governance
    status: MemeticStatus = MemeticStatus.RAW
    confidence_score: float = 1.0
    salience_score: float = 0.5
    access_count: int = 0
    access_control: Dict[str, Any] = field(default_factory=dict)
    lifespan_policy: Dict[str, Any] = field(default_factory=dict)

    # Relational Links
    links: List[MemeticLink] = field(default_factory=list)

    # Quality Metrics
    validation_score: float = 0.0
    consistency_score: float = 0.0
    relevance_score: float = 0.0


@dataclass
class MemeticUnit:
    """Universal container for all memory types with rich metadata."""

    # Core Components
    metadata: MemeticMetadata
    payload: Any  # Modality-agnostic content

    def __post_init__(self):
        """Initialize derived fields and validate structure."""
        if not self.metadata.unit_id:
            self.metadata.unit_id = uuid4()

        if not self.metadata.timestamp_created:
            self.metadata.timestamp_created = datetime.now()

        # Generate content hash if not provided
        if not self.metadata.content_hash and self.payload:
            self.metadata.content_hash = self._generate_content_hash()

        # Update access timestamp
        self.metadata.timestamp_accessed = datetime.now()
        self.metadata.access_count += 1

    def _generate_content_hash(self) -> str:
        """Generate hash of payload content for deduplication."""
        import hashlib
        import json

        # Normalize payload for consistent hashing
        if isinstance(self.payload, (dict, list)):
            normalized = json.dumps(self.payload, sort_keys=True)
        elif isinstance(self.payload, str):
            normalized = self.payload
        else:
            normalized = str(self.payload)

        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def add_link(self, target_id: UUID, relationship_type: str, strength: float = 1.0, **metadata):
        """Add a relationship to another memetic unit."""
        link = MemeticLink(
            target_id=target_id,
            relationship_type=relationship_type,
            strength=strength,
            metadata=metadata
        )
        self.metadata.links.append(link)

        logger.debug(f"Added link from {self.metadata.unit_id} to {target_id} with type {relationship_type}")

    def update_salience(self, context: Dict[str, Any]) -> None:
        """Update salience score based on context and usage patterns."""
        base_salience = self.metadata.salience_score

        # Boost salience for recent access
        time_factor = self._calculate_time_factor()

        # Boost salience for relevant context
        context_factor = self._calculate_context_factor(context)

        # Boost salience for high confidence
        confidence_factor = self.metadata.confidence_score

        # Calculate new salience
        new_salience = (base_salience * 0.6 +
                       time_factor * 0.2 +
                       context_factor * 0.15 +
                       confidence_factor * 0.05)

        self.metadata.salience_score = min(1.0, max(0.0, new_salience))

    def _calculate_time_factor(self) -> float:
        """Calculate time-based salience factor."""
        if not self.metadata.timestamp_accessed:
            return 0.0

        hours_since_access = (datetime.now() - self.metadata.timestamp_accessed).total_seconds() / 3600

        # Exponential decay with half-life of 24 hours
        return math.exp(-hours_since_access / 24.0)

    def _calculate_context_factor(self, context: Dict[str, Any]) -> float:
        """Calculate context relevance factor."""
        if not context or not self.metadata.keywords:
            return 0.5

        # Check keyword overlap with context
        context_keywords = set()
        for value in context.values():
            if isinstance(value, str):
                context_keywords.update(value.lower().split())

        unit_keywords = set(word.lower() for word in self.metadata.keywords)

        if not context_keywords or not unit_keywords:
            return 0.5

        overlap = len(context_keywords.intersection(unit_keywords))
        return overlap / len(unit_keywords) if unit_keywords else 0.5

    def is_expired(self) -> bool:
        """Check if unit has exceeded its lifespan policy."""
        if not self.metadata.lifespan_policy:
            return False

        policy = self.metadata.lifespan_policy

        # Check time-based expiration
        if "max_age_hours" in policy:
            max_age = policy["max_age_hours"]
            age_hours = (datetime.now() - self.metadata.timestamp_created).total_seconds() / 3600
            if age_hours > max_age:
                return True

        # Check access-based expiration
        if "max_inactive_hours" in policy:
            if self.metadata.timestamp_accessed:
                inactive_hours = (datetime.now() - self.metadata.timestamp_accessed).total_seconds() / 3600
                if inactive_hours > policy["max_inactive_hours"]:
                    return True

        return False

    def get_age_hours(self) -> float:
        """Get age of unit in hours."""
        return (datetime.now() - self.metadata.timestamp_created).total_seconds() / 3600

    def get_inactive_hours(self) -> float:
        """Get time since last access in hours."""
        if not self.metadata.timestamp_accessed:
            return self.get_age_hours()
        return (datetime.now() - self.metadata.timestamp_accessed).total_seconds() / 3600

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metadata": {
                "unit_id": str(self.metadata.unit_id),
                "parent_id": str(self.metadata.parent_id) if self.metadata.parent_id else None,
                "source": self.metadata.source.value,
                "timestamp_created": self.metadata.timestamp_created.isoformat(),
                "timestamp_accessed": self.metadata.timestamp_accessed.isoformat() if self.metadata.timestamp_accessed else None,
                "timestamp_modified": self.metadata.timestamp_modified.isoformat() if self.metadata.timestamp_modified else None,
                "cognitive_type": self.metadata.cognitive_type.value,
                "content_hash": self.metadata.content_hash,
                "semantic_vector": self.metadata.semantic_vector,
                "keywords": self.metadata.keywords,
                "topic": self.metadata.topic,
                "summary": self.metadata.summary,
                "status": self.metadata.status.value,
                "confidence_score": self.metadata.confidence_score,
                "salience_score": self.metadata.salience_score,
                "access_count": self.metadata.access_count,
                "access_control": self.metadata.access_control,
                "lifespan_policy": self.metadata.lifespan_policy,
                "links": [
                    {
                        "target_id": str(link.target_id),
                        "relationship_type": link.relationship_type,
                        "strength": link.strength,
                        "metadata": link.metadata
                    }
                    for link in self.metadata.links
                ],
                "validation_score": self.metadata.validation_score,
                "consistency_score": self.metadata.consistency_score,
                "relevance_score": self.metadata.relevance_score
            },
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemeticUnit":
        """Reconstruct from dictionary."""
        metadata_data = data["metadata"]

        # Reconstruct metadata
        metadata = MemeticMetadata(
            unit_id=UUID(metadata_data["unit_id"]),
            parent_id=UUID(metadata_data["parent_id"]) if metadata_data["parent_id"] else None,
            source=MemeticSource(metadata_data["source"]),
            timestamp_created=datetime.fromisoformat(metadata_data["timestamp_created"]),
            timestamp_accessed=datetime.fromisoformat(metadata_data["timestamp_accessed"]) if metadata_data["timestamp_accessed"] else None,
            timestamp_modified=datetime.fromisoformat(metadata_data["timestamp_modified"]) if metadata_data["timestamp_modified"] else None,
            cognitive_type=CognitiveType(metadata_data["cognitive_type"]),
            content_hash=metadata_data["content_hash"],
            semantic_vector=metadata_data["semantic_vector"],
            keywords=metadata_data["keywords"],
            topic=metadata_data["topic"],
            summary=metadata_data["summary"],
            status=MemeticStatus(metadata_data["status"]),
            confidence_score=metadata_data["confidence_score"],
            salience_score=metadata_data["salience_score"],
            access_count=metadata_data["access_count"],
            access_control=metadata_data["access_control"],
            lifespan_policy=metadata_data["lifespan_policy"],
            links=[
                MemeticLink(
                    target_id=UUID(link["target_id"]),
                    relationship_type=link["relationship_type"],
                    strength=link["strength"],
                    metadata=link["metadata"]
                )
                for link in metadata_data["links"]
            ],
            validation_score=metadata_data["validation_score"],
            consistency_score=metadata_data["consistency_score"],
            relevance_score=metadata_data["relevance_score"]
        )

        return cls(metadata=metadata, payload=data["payload"])


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
