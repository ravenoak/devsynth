"""
DevSynth Promise System API Specification.

This module defines the core interface for the Promise System, which provides
a capability declaration, verification, and authorization framework for agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Any, Union
from enum import Enum
from dataclasses import dataclass
import uuid


class PromiseState(Enum):
    """Represents the possible states of a Promise."""
    PENDING = "pending"       # Promise is created but not yet fulfilled
    FULFILLED = "fulfilled"   # Promise has been successfully fulfilled
    REJECTED = "rejected"     # Promise has failed to be fulfilled
    CANCELLED = "cancelled"   # Promise has been cancelled before fulfillment


class PromiseType(Enum):
    """Types of promises that can be made in the system."""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    TEST_EXECUTION = "test_execution"
    LLM_QUERY = "llm_query"
    MEMORY_ACCESS = "memory_access"
    AGENT_COMMUNICATION = "agent_communication"
    ORCHESTRATION = "orchestration"
    SYSTEM = "system"


@dataclass
class PromiseMetadata:
    """Metadata associated with a Promise."""
    created_at: float  # Unix timestamp
    owner_id: str      # ID of the agent that created the promise
    context_id: str    # Context or task ID this promise belongs to
    tags: List[str]    # User-defined tags for filtering and organization
    trace_id: str      # For distributed tracing
    priority: int = 1  # Priority level (higher is more important)


@dataclass
class Promise:
    """
    Represents a Promise in the system - a declaration of intent to perform
    a capability with specific parameters and constraints.
    """
    id: str                           # Unique identifier
    type: PromiseType                 # Type of capability
    parameters: Dict[str, Any]        # Parameters for this promise
    state: PromiseState               # Current state
    metadata: PromiseMetadata         # Associated metadata
    result: Optional[Any] = None      # Result when fulfilled
    error: Optional[str] = None       # Error message if rejected
    parent_id: Optional[str] = None   # Parent promise if this is a sub-promise
    children_ids: List[str] = None    # Child promises if this has sub-promises

    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []


class IPromiseManager(ABC):
    """
    Interface for the Promise Manager which handles creation, fulfillment,
    rejection and tracking of promises throughout the system.
    """

    @abstractmethod
    def create_promise(
        self,
        type: PromiseType,
        parameters: Dict[str, Any],
        owner_id: str,
        context_id: str,
        tags: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
        priority: int = 1
    ) -> Promise:
        """
        Create a new promise with the given parameters.

        Args:
            type: The type of capability being promised
            parameters: Specific parameters for this promise
            owner_id: ID of the agent making the promise
            context_id: Context or task ID
            tags: Optional tags for filtering
            parent_id: Optional parent promise ID
            priority: Importance level (default 1)

        Returns:
            A newly created Promise in PENDING state
        """
        pass

    @abstractmethod
    def fulfill_promise(self, promise_id: str, result: Any) -> Promise:
        """
        Mark a promise as fulfilled with the given result.

        Args:
            promise_id: ID of the promise to fulfill
            result: The result of the fulfilled promise

        Returns:
            The updated Promise in FULFILLED state
        """
        pass

    @abstractmethod
    def reject_promise(self, promise_id: str, error: str) -> Promise:
        """
        Mark a promise as rejected with the given error.

        Args:
            promise_id: ID of the promise to reject
            error: Description of why the promise was rejected

        Returns:
            The updated Promise in REJECTED state
        """
        pass

    @abstractmethod
    def cancel_promise(self, promise_id: str, reason: str) -> Promise:
        """
        Cancel a pending promise.

        Args:
            promise_id: ID of the promise to cancel
            reason: Reason for cancellation

        Returns:
            The updated Promise in CANCELLED state
        """
        pass

    @abstractmethod
    def get_promise(self, promise_id: str) -> Promise:
        """
        Retrieve a promise by its ID.

        Args:
            promise_id: ID of the promise to retrieve

        Returns:
            The Promise object
        """
        pass

    @abstractmethod
    def list_promises(
        self,
        owner_id: Optional[str] = None,
        context_id: Optional[str] = None,
        state: Optional[PromiseState] = None,
        type: Optional[PromiseType] = None,
        tags: Optional[List[str]] = None,
        parent_id: Optional[str] = None
    ) -> List[Promise]:
        """
        List promises matching the given filters.

        Args:
            owner_id: Filter by owner
            context_id: Filter by context
            state: Filter by state
            type: Filter by promise type
            tags: Filter by tags (any match)
            parent_id: Filter by parent promise

        Returns:
            List of matching Promises
        """
        pass

    @abstractmethod
    def create_child_promise(
        self,
        parent_id: str,
        type: PromiseType,
        parameters: Dict[str, Any],
        owner_id: str,
        tags: Optional[List[str]] = None,
        priority: int = 1
    ) -> Promise:
        """
        Create a child promise linked to a parent promise.

        Args:
            parent_id: ID of the parent promise
            type: Type of capability
            parameters: Parameters for this promise
            owner_id: ID of the agent making the promise
            tags: Optional tags
            priority: Importance level

        Returns:
            A newly created Promise linked to its parent
        """
        pass

    @abstractmethod
    def validate_promise_chain(self, root_promise_id: str) -> bool:
        """
        Validate the integrity of a promise chain (parent-child relationships).

        Args:
            root_promise_id: ID of the root promise in the chain

        Returns:
            True if the chain is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_promise_chain(self, promise_id: str) -> List[Promise]:
        """
        Get all promises in a chain (ancestors and descendants).

        Args:
            promise_id: ID of any promise in the chain

        Returns:
            List of all related Promises in the chain
        """
        pass


class IPromiseAuthority(ABC):
    """
    Interface for the Promise Authority which handles authorization
    and access control for promises and capabilities.
    """

    @abstractmethod
    def can_create(
        self,
        agent_id: str,
        promise_type: PromiseType,
        parameters: Dict[str, Any]
    ) -> bool:
        """
        Check if an agent is authorized to create a promise of the given type.

        Args:
            agent_id: ID of the agent requesting authorization
            promise_type: Type of capability being requested
            parameters: Specific parameters for this promise

        Returns:
            True if authorized, False otherwise
        """
        pass

    @abstractmethod
    def can_fulfill(self, agent_id: str, promise_id: str) -> bool:
        """
        Check if an agent is authorized to fulfill a specific promise.

        Args:
            agent_id: ID of the agent attempting fulfillment
            promise_id: ID of the promise to be fulfilled

        Returns:
            True if authorized, False otherwise
        """
        pass

    @abstractmethod
    def can_reject(self, agent_id: str, promise_id: str) -> bool:
        """
        Check if an agent is authorized to reject a specific promise.

        Args:
            agent_id: ID of the agent attempting rejection
            promise_id: ID of the promise to be rejected

        Returns:
            True if authorized, False otherwise
        """
        pass

    @abstractmethod
    def can_cancel(self, agent_id: str, promise_id: str) -> bool:
        """
        Check if an agent is authorized to cancel a specific promise.

        Args:
            agent_id: ID of the agent attempting cancellation
            promise_id: ID of the promise to be cancelled

        Returns:
            True if authorized, False otherwise
        """
        pass

    @abstractmethod
    def can_delegate(
        self,
        agent_id: str,
        promise_id: str,
        delegate_to: str
    ) -> bool:
        """
        Check if an agent is authorized to delegate a promise to another agent.

        Args:
            agent_id: ID of the agent attempting delegation
            promise_id: ID of the promise to be delegated
            delegate_to: ID of the agent receiving the delegation

        Returns:
            True if authorized, False otherwise
        """
        pass

    @abstractmethod
    def register_capability(
        self,
        agent_id: str,
        promise_type: PromiseType,
        constraints: Dict[str, Any]
    ) -> bool:
        """
        Register an agent as capable of handling promises of a specific type.

        Args:
            agent_id: ID of the agent registering capability
            promise_type: Type of capability being registered
            constraints: Constraints on parameters (e.g., limits)

        Returns:
            True if registration successful, False otherwise
        """
        pass

    @abstractmethod
    def list_agent_capabilities(self, agent_id: str) -> Dict[PromiseType, Dict]:
        """
        List all capabilities registered for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dictionary mapping capability types to their constraints
        """
        pass
