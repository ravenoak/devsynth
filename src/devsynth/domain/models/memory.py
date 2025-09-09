from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from devsynth.exceptions import DevSynthError
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
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


# Alias for backward compatibility and for use in tests
MemoryItemType = MemoryType


@dataclass
class MemoryItem:
    """A single item stored in memory."""

    id: str
    content: Any
    memory_type: MemoryType
    metadata: Dict[str, Any] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class MemoryVector:
    """A vector representation of a memory item."""

    id: str
    content: Any
    embedding: List[float]
    metadata: Dict[str, Any] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
