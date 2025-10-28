"""
Concrete implementation of the Promise system.
Provides a Promise class that implements the PromiseInterface.
"""

import logging
import uuid
from enum import Enum, auto
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from collections.abc import Callable

from devsynth.application.promises.interface import PromiseInterface
from devsynth.exceptions import DevSynthError

# Setup logger
logger = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")


from .interface import PromiseState


class PromiseError(DevSynthError):
    """Base class for Promise-related errors."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Promise error")


class PromiseStateError(PromiseError):
    """Error raised when an invalid state transition is attempted."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Invalid promise state")


class Promise(PromiseInterface[T], Generic[T]):
    """
    Concrete implementation of the Promise interface.

    This class implements an asynchronous promise pattern similar to JavaScript Promises,
    allowing for capability declaration, chaining, and error handling.

    DevSynth can analyze Promise instances to trace capability usage, dependency chains,
    and potential issues in asynchronous workflows.

    Attributes:
        _state (PromiseState): Current state of the promise (pending, fulfilled, rejected)
        _value (T): Value with which the promise was fulfilled
        _reason (Exception): Reason why the promise was rejected
        _on_fulfilled (List[Callable]): Callbacks to execute when the promise is fulfilled
        _on_rejected (List[Callable]): Callbacks to execute when the promise is rejected
        _id (str): Unique identifier for the promise, used for tracing and debugging
        _metadata (Dict[str, Any]): Additional metadata for DevSynth analysis
    """

    def __init__(self):
        """Initialize a new Promise in the pending state."""
        self._state: PromiseState = PromiseState.PENDING
        self._value: T | None = None
        self._reason: Exception | None = None
        self._on_fulfilled: list[Callable] = []
        self._on_rejected: list[Callable] = []
        self._id: str = str(uuid.uuid4())
        self._parent_id: str | None = None
        self._children_ids: list[str] = []
        self._metadata: dict[str, Any] = {
            "created_at": None,  # Will be set by calling code
            "resolved_at": None,
            "rejected_at": None,
            "source": None,  # Component that created this promise
            "capability": None,  # Capability this promise represents
            "tags": [],  # User-defined tags for filtering and grouping
        }

        logger.debug(f"Promise {self._id} created in PENDING state")

    @property
    def id(self) -> str:
        """Get the unique identifier of this promise."""
        return self._id

    @property
    def state(self) -> PromiseState:
        """Get the current state of this promise."""
        return self._state

    @property
    def is_pending(self) -> bool:
        """Check if the promise is in the pending state."""
        return self._state == PromiseState.PENDING

    @property
    def is_fulfilled(self) -> bool:
        """Check if the promise is in the fulfilled state."""
        return self._state == PromiseState.FULFILLED

    @property
    def is_rejected(self) -> bool:
        """Check if the promise is in the rejected state."""
        return self._state == PromiseState.REJECTED

    @property
    def value(self) -> T:
        """
        Get the fulfillment value of this promise.

        Returns:
            The value with which the promise was fulfilled.

        Raises:
            PromiseStateError: If the promise is not in the fulfilled state.
        """
        if self._state != PromiseState.FULFILLED:
            raise PromiseStateError(
                f"Cannot get value of promise in state {self._state}"
            )
        return self._value

    @property
    def reason(self) -> Exception:
        """
        Get the rejection reason of this promise.

        Returns:
            The reason why the promise was rejected.

        Raises:
            PromiseStateError: If the promise is not in the rejected state.
        """
        if self._state != PromiseState.REJECTED:
            raise PromiseStateError(
                f"Cannot get reason of promise in state {self._state}"
            )
        return self._reason

    @property
    def parent_id(self) -> str | None:
        """
        Get the ID of the parent promise, if any.

        Returns:
            The ID of the parent promise, or None if this promise has no parent.
        """
        return self._parent_id

    @parent_id.setter
    def parent_id(self, value: str | None) -> None:
        """
        Set the ID of the parent promise.

        Args:
            value: The ID of the parent promise, or None to remove the parent.
        """
        self._parent_id = value

    @property
    def children_ids(self) -> list[str]:
        """
        Get the IDs of the child promises, if any.

        Returns:
            A list of IDs of child promises.
        """
        return self._children_ids

    def add_child_id(self, child_id: str) -> None:
        """
        Add a child promise ID to this promise.

        Args:
            child_id: The ID of the child promise to add.
        """
        if child_id not in self._children_ids:
            self._children_ids.append(child_id)
            logger.debug(f"Added child promise {child_id} to parent {self._id}")

    def set_metadata(self, key: str, value: Any) -> "Promise[T]":
        """
        Set a metadata value for DevSynth analysis.

        Args:
            key: The metadata key to set
            value: The value to associate with the key

        Returns:
            Self, for chaining
        """
        self._metadata[key] = value
        return self

    def get_metadata(self, key: str) -> Any:
        """
        Get a metadata value.

        Args:
            key: The metadata key to retrieve

        Returns:
            The associated value, or None if the key does not exist
        """
        return self._metadata.get(key)

    def then(
        self,
        on_fulfilled: Callable[[T], S],
        on_rejected: Callable[[Exception], S] | None = None,
    ) -> "Promise[S]":
        """
        Attaches callbacks for the resolution and/or rejection of the Promise.

        Args:
            on_fulfilled: Function to be called when the Promise is fulfilled.
            on_rejected: Optional function to be called when the Promise is rejected.

        Returns:
            A new Promise resolving with the return value of the called callback.
        """
        result_promise: Promise[S] = Promise()

        # Define handlers that will call the appropriate callback and resolve/reject the result promise
        def handle_fulfill(value: T) -> None:
            if on_fulfilled is None:
                result_promise.resolve(value)  # type: ignore
                return

            try:
                result = on_fulfilled(value)
                result_promise.resolve(result)
            except Exception as e:
                result_promise.reject(e)

        def handle_reject(reason: Exception) -> None:
            if on_rejected is None:
                result_promise.reject(reason)
                return

            try:
                result = on_rejected(reason)
                result_promise.resolve(result)
            except Exception as e:
                result_promise.reject(e)

        # If this promise is already fulfilled or rejected, call the appropriate handler immediately
        if self._state == PromiseState.FULFILLED:
            handle_fulfill(self._value)
        elif self._state == PromiseState.REJECTED:
            handle_reject(self._reason)
        else:
            # Otherwise, add the handlers to the callbacks to be called when this promise is settled
            self._on_fulfilled.append(handle_fulfill)
            self._on_rejected.append(handle_reject)

        # Link the result promise to this one for DevSynth tracing
        result_promise.set_metadata("parent_promise_id", self._id)

        logger.debug(f"Promise {self._id} chained to new promise {result_promise.id}")
        return result_promise

    def catch(self, on_rejected: Callable[[Exception], S]) -> "Promise[S]":
        """
        Attaches a callback for only the rejection of the Promise.

        Args:
            on_rejected: Function to be called when the Promise is rejected.

        Returns:
            A new Promise resolving with the return value of the on_rejected callback.
        """
        return self.then(lambda x: x, on_rejected)  # type: ignore

    def resolve(self, value: T) -> None:
        """
        Resolves the promise with a given value.
        To be used by the promise's creator.

        DevSynth Tracing Hint: This transition is logged with promise ID and resolved value.

        Args:
            value: The value with which to resolve the promise

        Raises:
            PromiseStateError: If the promise is already fulfilled or rejected
        """
        if self._state != PromiseState.PENDING:
            raise PromiseStateError(f"Cannot resolve promise in state {self._state}")

        self._state = PromiseState.FULFILLED
        self._value = value
        self._metadata["resolved_at"] = None  # Will be set by calling code

        logger.debug(f"Promise {self._id} resolved with value: {value}")

        # Call all the on_fulfilled callbacks with the value
        for callback in self._on_fulfilled:
            try:
                callback(value)
            except Exception as e:
                logger.error(f"Error in promise callback: {e}")

        # Clear the callback lists to avoid memory leaks
        self._on_fulfilled = []
        self._on_rejected = []

    def reject(self, reason: Exception) -> None:
        """
        Rejects the promise with a given reason (error).
        To be used by the promise's creator.

        DevSynth Tracing Hint: This transition is logged with promise ID and rejection reason.

        Args:
            reason: The reason why the promise was rejected

        Raises:
            PromiseStateError: If the promise is already fulfilled or rejected
        """
        if self._state != PromiseState.PENDING:
            raise PromiseStateError(f"Cannot reject promise in state {self._state}")

        self._state = PromiseState.REJECTED
        self._reason = reason
        self._metadata["rejected_at"] = None  # Will be set by calling code

        logger.debug(f"Promise {self._id} rejected with reason: {reason}")

        # Call all the on_rejected callbacks with the reason
        for callback in self._on_rejected:
            try:
                callback(reason)
            except Exception as e:
                logger.error(f"Error in promise callback: {e}")

        # Clear the callback lists to avoid memory leaks
        self._on_fulfilled = []
        self._on_rejected = []

    @staticmethod
    def resolve_value(value: T) -> "Promise[T]":
        """
        Creates a Promise that is resolved with a given value.

        Args:
            value: Value to resolve the promise with

        Returns:
            A new Promise that is already resolved with the given value
        """
        promise = Promise[T]()
        promise.resolve(value)
        return promise

    @staticmethod
    def reject_with(reason: Exception) -> "Promise[Any]":
        """
        Creates a Promise that is rejected with a given reason.

        Args:
            reason: Reason to reject the promise with

        Returns:
            A new Promise that is already rejected with the given reason
        """
        promise = Promise[Any]()
        promise.reject(reason)
        return promise

    @staticmethod
    def all(promises: list["Promise[Any]"]) -> "Promise[List[Any]]":
        """
        Returns a promise that resolves when all of the promises in the iterable argument
        have resolved, or rejects with the reason of the first passed promise that rejects.

        Args:
            promises: List of promises to wait for

        Returns:
            A promise that resolves with a list of all the resolved values
        """
        if not promises:
            return Promise.resolve_value([])

        result_promise = Promise[list[Any]]()
        results = [None] * len(promises)
        pending_count = len(promises)

        def on_fulfill(index: int) -> Callable[[Any], None]:
            def handle(value: Any) -> None:
                nonlocal pending_count
                results[index] = value
                pending_count -= 1

                if pending_count == 0:
                    result_promise.resolve(results)

            return handle

        def on_reject(reason: Exception) -> None:
            result_promise.reject(reason)

        for i, promise in enumerate(promises):
            promise.then(on_fulfill(i), on_reject)

        return result_promise

    @staticmethod
    def race(promises: list["Promise[T]"]) -> "Promise[T]":
        """
        Returns a promise that resolves or rejects as soon as one of the promises in
        the iterable resolves or rejects, with the value or reason from that promise.

        Args:
            promises: List of promises to race

        Returns:
            A promise that resolves or rejects with the value/reason of the first settled promise
        """
        if not promises:
            return Promise[T]()

        result_promise = Promise[T]()

        def on_fulfill(value: T) -> None:
            result_promise.resolve(value)

        def on_reject(reason: Exception) -> None:
            result_promise.reject(reason)

        for promise in promises:
            promise.then(on_fulfill, on_reject)

        return result_promise
