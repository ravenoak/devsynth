"""
DevSynth Promise System API Specification.

This module defines the core interface for the Promise System, which provides
a capability declaration, verification, and authorization framework for agents.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, Union
from collections.abc import Callable

from devsynth.exceptions import PromiseStateError

T = TypeVar("T")
S = TypeVar("S")


class PromiseInterface(Generic[T], ABC):
    """
    Interface for Promise objects in the system.
    Defines the contract that all Promise implementations must follow.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Get the unique identifier of this promise."""
        raise NotImplementedError

    @property
    @abstractmethod
    def state(self) -> "PromiseState":
        """Get the current state of this promise."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_pending(self) -> bool:
        """Check if the promise is in the pending state."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_fulfilled(self) -> bool:
        """Check if the promise is in the fulfilled state."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_rejected(self) -> bool:
        """Check if the promise is in the rejected state."""
        raise NotImplementedError

    @property
    @abstractmethod
    def value(self) -> T:
        """
        Get the fulfillment value of this promise.

        Returns:
            The value with which the promise was fulfilled.

        Raises:
            PromiseStateError: If the promise is not in the fulfilled state.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def reason(self) -> Exception:
        """
        Get the rejection reason of this promise.

        Returns:
            The reason why the promise was rejected.

        Raises:
            PromiseStateError: If the promise is not in the rejected state.
        """
        raise NotImplementedError

    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> "PromiseInterface[T]":
        """
        Set a metadata value for DevSynth analysis.

        Args:
            key: The metadata key to set
            value: The value to associate with the key

        Returns:
            Self, for chaining
        """
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self, key: str) -> Any:
        """
        Get a metadata value.

        Args:
            key: The metadata key to retrieve

        Returns:
            The associated value, or None if the key does not exist
        """
        raise NotImplementedError

    @abstractmethod
    def then(
        self,
        on_fulfilled: Callable[[T], S],
        on_rejected: Callable[[Exception], S] | None = None,
    ) -> "PromiseInterface[S]":
        """
        Attaches callbacks for the resolution and/or rejection of the Promise.

        Args:
            on_fulfilled: Function to be called when the Promise is fulfilled.
            on_rejected: Optional function to be called when the Promise is rejected.

        Returns:
            A new Promise resolving with the return value of the called callback.
        """
        raise NotImplementedError

    @abstractmethod
    def catch(self, on_rejected: Callable[[Exception], S]) -> "PromiseInterface[S]":
        """
        Attaches a callback for only the rejection of the Promise.

        Args:
            on_rejected: Function to be called when the Promise is rejected.

        Returns:
            A new Promise resolving with the return value of the on_rejected callback.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve(self, value: T) -> None:
        """
        Resolves the promise with a given value.
        To be used by the promise's creator.

        Args:
            value: The value with which to resolve the promise

        Raises:
            PromiseStateError: If the promise is already fulfilled or rejected
        """
        raise NotImplementedError

    @abstractmethod
    def reject(self, reason: Exception) -> None:
        """
        Rejects the promise with a given reason (error).
        To be used by the promise's creator.

        Args:
            reason: The reason why the promise was rejected

        Raises:
            PromiseStateError: If the promise is already fulfilled or rejected
        """
        raise NotImplementedError


class PromiseState(Enum):
    """Represents the possible states of a Promise."""

    PENDING = "pending"  # Promise is created but not yet fulfilled
    FULFILLED = "fulfilled"  # Promise has been successfully fulfilled
    REJECTED = "rejected"  # Promise has failed to be fulfilled
    CANCELLED = "cancelled"  # Promise has been cancelled before fulfillment


class BasicPromise(PromiseInterface[T], Generic[T]):
    """Simple implementation of :class:`PromiseInterface`."""

    def __init__(self) -> None:
        self._state: PromiseState = PromiseState.PENDING
        self._value: T | None = None
        self._reason: Exception | None = None
        self._on_fulfilled: list[Callable[[T], Any]] = []
        self._on_rejected: list[Callable[[Exception], Any]] = []
        self._id: str = str(uuid.uuid4())
        self._metadata: dict[str, Any] = {}
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def id(self) -> str:
        """Return the unique identifier for this promise."""
        return self._id

    @property
    def state(self) -> PromiseState:
        """Return the current state of the promise."""
        return self._state

    @property
    def is_pending(self) -> bool:
        return self._state == PromiseState.PENDING

    @property
    def is_fulfilled(self) -> bool:
        return self._state == PromiseState.FULFILLED

    @property
    def is_rejected(self) -> bool:
        return self._state == PromiseState.REJECTED

    @property
    def value(self) -> T:
        if self._state != PromiseState.FULFILLED:
            raise PromiseStateError(
                f"Cannot get value of promise in state {self._state}",
                promise_id=self._id,
            )
        return self._value  # type: ignore

    @property
    def reason(self) -> Exception:
        if self._state != PromiseState.REJECTED:
            raise PromiseStateError(
                f"Cannot get reason of promise in state {self._state}",
                promise_id=self._id,
            )
        return self._reason  # type: ignore

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------
    def set_metadata(self, key: str, value: Any) -> "BasicPromise[T]":
        self._metadata[key] = value
        return self

    def get_metadata(self, key: str) -> Any:
        return self._metadata.get(key)

    # ------------------------------------------------------------------
    # Promise chaining
    # ------------------------------------------------------------------
    def then(
        self,
        on_fulfilled: Callable[[T], S],
        on_rejected: Callable[[Exception], S] | None = None,
    ) -> "BasicPromise[S]":
        result_promise: BasicPromise[S] = BasicPromise()

        def handle_fulfill(value: T) -> None:
            if on_fulfilled is None:
                result_promise.resolve(value)  # type: ignore[arg-type]
                return
            try:
                result = on_fulfilled(value)
                result_promise.resolve(result)
            except Exception as exc:  # pragma: no cover - defensive
                result_promise.reject(exc)

        def handle_reject(reason: Exception) -> None:
            if on_rejected is None:
                result_promise.reject(reason)
                return
            try:
                result = on_rejected(reason)
                result_promise.resolve(result)
            except Exception as exc:  # pragma: no cover - defensive
                result_promise.reject(exc)

        if self._state == PromiseState.FULFILLED:
            handle_fulfill(self._value)  # type: ignore[arg-type]
        elif self._state == PromiseState.REJECTED:
            handle_reject(self._reason)  # type: ignore[arg-type]
        else:
            self._on_fulfilled.append(handle_fulfill)
            self._on_rejected.append(handle_reject)

        return result_promise

    def catch(self, on_rejected: Callable[[Exception], S]) -> "BasicPromise[S]":
        return self.then(lambda v: v, on_rejected)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------
    def resolve(self, value: T) -> None:
        if self._state != PromiseState.PENDING:
            raise PromiseStateError(
                f"Cannot resolve promise in state {self._state}",
                promise_id=self._id,
            )
        self._state = PromiseState.FULFILLED
        self._value = value
        for cb in self._on_fulfilled:
            try:
                cb(value)
            except Exception as exc:  # pragma: no cover - defensive
                self._logger.error("Error in promise callback: %s", exc)
        self._on_fulfilled.clear()
        self._on_rejected.clear()

    def reject(self, reason: Exception) -> None:
        if self._state != PromiseState.PENDING:
            raise PromiseStateError(
                f"Cannot reject promise in state {self._state}",
                promise_id=self._id,
            )
        self._state = PromiseState.REJECTED
        self._reason = reason
        for cb in self._on_rejected:
            try:
                cb(reason)
            except Exception as exc:  # pragma: no cover - defensive
                self._logger.error("Error in promise callback: %s", exc)
        self._on_fulfilled.clear()
        self._on_rejected.clear()


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
    owner_id: str  # ID of the agent that created the promise
    context_id: str  # Context or task ID this promise belongs to
    tags: list[str]  # User-defined tags for filtering and organization
    trace_id: str  # For distributed tracing
    priority: int = 1  # Priority level (higher is more important)


@dataclass
class Promise:
    """
    Represents a Promise in the system - a declaration of intent to perform
    a capability with specific parameters and constraints.
    """

    id: str  # Unique identifier
    type: PromiseType  # Type of capability
    parameters: dict[str, Any]  # Parameters for this promise
    state: PromiseState  # Current state
    metadata: PromiseMetadata  # Associated metadata
    result: Any | None = None  # Result when fulfilled
    error: str | None = None  # Error message if rejected
    parent_id: str | None = None  # Parent promise if this is a sub-promise
    children_ids: list[str] = None  # Child promises if this has sub-promises

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
        parameters: dict[str, Any],
        owner_id: str,
        context_id: str,
        tags: list[str] | None = None,
        parent_id: str | None = None,
        priority: int = 1,
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
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError

    @abstractmethod
    def get_promise(self, promise_id: str) -> Promise:
        """
        Retrieve a promise by its ID.

        Args:
            promise_id: ID of the promise to retrieve

        Returns:
            The Promise object
        """
        raise NotImplementedError

    @abstractmethod
    def list_promises(
        self,
        owner_id: str | None = None,
        context_id: str | None = None,
        state: PromiseState | None = None,
        type: PromiseType | None = None,
        tags: list[str] | None = None,
        parent_id: str | None = None,
    ) -> list[Promise]:
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
        raise NotImplementedError

    @abstractmethod
    def create_child_promise(
        self,
        parent_id: str,
        type: PromiseType,
        parameters: dict[str, Any],
        owner_id: str,
        tags: list[str] | None = None,
        priority: int = 1,
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
        raise NotImplementedError

    @abstractmethod
    def validate_promise_chain(self, root_promise_id: str) -> bool:
        """
        Validate the integrity of a promise chain (parent-child relationships).

        Args:
            root_promise_id: ID of the root promise in the chain

        Returns:
            True if the chain is valid, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_promise_chain(self, promise_id: str) -> list[Promise]:
        """
        Get all promises in a chain (ancestors and descendants).

        Args:
            promise_id: ID of any promise in the chain

        Returns:
            List of all related Promises in the chain
        """
        raise NotImplementedError


class IPromiseAuthority(ABC):
    """
    Interface for the Promise Authority which handles authorization
    and access control for promises and capabilities.
    """

    @abstractmethod
    def can_create(
        self, agent_id: str, promise_type: PromiseType, parameters: dict[str, Any]
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
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError

    @abstractmethod
    def can_delegate(self, agent_id: str, promise_id: str, delegate_to: str) -> bool:
        """
        Check if an agent is authorized to delegate a promise to another agent.

        Args:
            agent_id: ID of the agent attempting delegation
            promise_id: ID of the promise to be delegated
            delegate_to: ID of the agent receiving the delegation

        Returns:
            True if authorized, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def register_capability(
        self, agent_id: str, promise_type: PromiseType, constraints: dict[str, Any]
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
        raise NotImplementedError

    @abstractmethod
    def list_agent_capabilities(self, agent_id: str) -> dict[PromiseType, dict]:
        """
        List all capabilities registered for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dictionary mapping capability types to their constraints
        """
        raise NotImplementedError
