"""
Agent integration for the Promise System.

This module provides utilities for integrating the Promise System with DevSynth agents,
allowing agents to declare capabilities, request capabilities from other agents,
and track promise fulfillment.
"""

import logging
import threading
import time
import uuid
from datetime import UTC, datetime
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from devsynth.exceptions import DevSynthError

from .broker import (
    CapabilityMetadata,
    CapabilityNotFoundError,
    PromiseBroker,
    UnauthorizedAccessError,
)
from .implementation import Promise
from .interface import PromiseType

# Setup logger
logger = logging.getLogger(__name__)


class AgentCapabilityError(DevSynthError):
    """Base class for agent capability errors."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Agent capability error")


class CapabilityHandler:
    """
    Handles capability registration, execution, and fulfillment for an agent.

    This class wraps a function or method that implements a capability,
    and manages the Promise lifecycle associated with that capability.
    """

    def __init__(
        self,
        agent_id: str,
        capability_name: str,
        handler_func: Callable,
        description: str,
        parameters: Dict[str, str] = None,
        tags: List[str] = None,
        authorized_requesters: Set[str] = None,
    ):
        """
        Initialize a capability handler.

        Args:
            agent_id: The ID of the agent that provides this capability
            capability_name: The name of the capability
            handler_func: The function that implements the capability
            description: A description of what the capability does
            parameters: A dictionary mapping parameter names to their types
            tags: A list of tags for categorizing the capability
            authorized_requesters: Set of agent IDs that are authorized to use this capability
        """
        self.agent_id = agent_id
        self.capability_name = capability_name
        self.handler_func = handler_func
        self.description = description
        self.parameters = parameters or {}
        self.tags = tags or []
        self.authorized_requesters = authorized_requesters

        # Holds active promises for this capability
        self._active_promises: Dict[str, Promise] = {}

    def __call__(self, *args, **kwargs) -> Any:
        """
        Execute the capability handler function.

        This should only be called internally by the agent. External callers
        should request the capability through the Promise system.

        Args:
            *args: Positional arguments to pass to the handler function
            **kwargs: Keyword arguments to pass to the handler function

        Returns:
            The result of the handler function
        """
        return self.handler_func(*args, **kwargs)

    def handle_request(self, promise: Promise, *args, **kwargs) -> None:
        """
        Handle a capability request by executing the handler function and resolving the promise.

        Args:
            promise: The promise to resolve with the result of the handler function
            *args: Positional arguments to pass to the handler function
            **kwargs: Keyword arguments to pass to the handler function
        """
        promise_id = promise.get_metadata("promise_id")
        if not promise_id:
            promise_id = str(uuid.uuid4())
            promise.set_metadata("promise_id", promise_id)

        # Store the promise for future reference
        self._active_promises[promise_id] = promise

        # Set metadata for execution tracking
        promise.set_metadata("execution_started_at", datetime.now(UTC).isoformat())

        try:
            # Execute the handler function
            result = self.handler_func(*args, **kwargs)

            # Set execution completed metadata
            promise.set_metadata(
                "execution_completed_at", datetime.now(UTC).isoformat()
            )

            # Resolve the promise with the result
            promise.resolve(result)
            logger.debug(
                f"Capability '{self.capability_name}' executed successfully for promise {promise_id}"
            )
        except Exception as e:
            # Set execution failed metadata
            promise.set_metadata("execution_failed_at", datetime.now(UTC).isoformat())
            promise.set_metadata("error_message", str(e))

            # Reject the promise with the exception
            promise.reject(e)
            logger.error(
                f"Capability '{self.capability_name}' execution failed for promise {promise_id}: {e}"
            )
        finally:
            # Clean up the promise reference
            if promise.is_fulfilled or promise.is_rejected:
                self._active_promises.pop(promise_id, None)


class PromiseAgentMixin:
    """
    Mixin for agents to integrate with the Promise system.

    This mixin provides methods for agents to:
    1. Register capabilities they provide
    2. Request capabilities from other agents
    3. Track promise fulfillment
    """

    def __init__(self, agent_id: str, broker: Optional[PromiseBroker] = None):
        """
        Initialize the Promise Agent Mixin.

        Args:
            agent_id: Unique identifier for this agent
            broker: PromiseBroker instance to use, or None to create a new one
        """
        self.agent_id = agent_id
        self.broker = broker or PromiseBroker()

        # Dictionary of capability handlers by name
        self._capability_handlers: Dict[str, CapabilityHandler] = {}

        # Dictionary of capability IDs by name
        self._capability_ids: Dict[str, str] = {}

        # Pending promises requested from other agents
        self._pending_requests: Dict[str, Promise] = {}

        logger.debug(f"Agent {agent_id} initialized with Promise integration")

    def register_capability(
        self,
        name: str,
        handler_func: Callable,
        description: str,
        parameters: Dict[str, str] = None,
        tags: List[str] = None,
        authorized_requesters: Set[str] = None,
    ) -> str:
        """
        Register a capability that this agent provides.

        Args:
            name: The name of the capability
            handler_func: Function or method that implements the capability
            description: A description of what the capability does
            parameters: A dictionary mapping parameter names to their types
            tags: A list of tags for categorizing the capability
            authorized_requesters: Set of agent IDs that are authorized to use this capability

        Returns:
            The ID of the registered capability

        Raises:
            CapabilityAlreadyRegisteredError: If a capability with the same name already exists
        """
        # Create a handler for this capability
        handler = CapabilityHandler(
            agent_id=self.agent_id,
            capability_name=name,
            handler_func=handler_func,
            description=description,
            parameters=parameters,
            tags=tags,
            authorized_requesters=authorized_requesters,
        )

        # Register the capability with the broker
        capability_id = self.broker.register_capability(
            name=name,
            description=description,
            provider_id=self.agent_id,
            parameters=parameters,
            tags=tags,
            authorized_requesters=authorized_requesters,
        )

        # Store the handler and capability ID
        self._capability_handlers[name] = handler
        self._capability_ids[name] = capability_id

        logger.debug(
            f"Agent {self.agent_id} registered capability '{name}' with ID {capability_id}"
        )

        return capability_id

    def unregister_capability(self, name: str) -> bool:
        """
        Unregister a capability that this agent provides.

        Args:
            name: The name of the capability to unregister

        Returns:
            True if the capability was unregistered, False if it wasn't found
        """
        if name not in self._capability_ids:
            return False

        capability_id = self._capability_ids[name]

        # Remove the capability from the broker
        result = self.broker.unregister_capability(capability_id)

        if result:
            # Remove the handler and capability ID
            self._capability_handlers.pop(name, None)
            self._capability_ids.pop(name, None)

            logger.debug(f"Agent {self.agent_id} unregistered capability '{name}'")

        return result

    def request_capability(
        self,
        name: str,
        provider_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Promise:
        """
        Request a capability from another agent.

        Args:
            name: The name of the requested capability
            provider_id: Optional provider ID to request from a specific agent
            tags: Optional tags to filter capabilities
            timeout: Maximum time (in seconds) to wait for the capability to be fulfilled
            **kwargs: Arguments to pass to the capability handler

        Returns:
            A Promise that will be fulfilled when the capability is exercised

        Raises:
            CapabilityNotFoundError: If no matching capability is found
            UnauthorizedAccessError: If this agent is not authorized to use the capability
        """
        # Request the capability from the broker
        promise = self.broker.request_capability(
            requester_id=self.agent_id, name=name, provider_id=provider_id, tags=tags
        )

        # Store the promise and arguments for tracking
        promise_id = promise.get_metadata("promise_id")
        self._pending_requests[promise_id] = promise

        # Store the arguments in metadata for the provider to access
        for key, value in kwargs.items():
            promise.set_metadata(f"arg_{key}", value)

        # If a timeout is specified, set up a timeout mechanism
        if timeout is not None:
            promise.set_metadata("timeout", timeout)
            promise.set_metadata("requested_at", time.time())

            # Start a timer to automatically reject the promise when the timeout expires
            def _timeout_reject() -> None:
                if promise.is_pending:
                    error_msg = f"Capability request timed out after {timeout} seconds"
                    promise.reject(TimeoutError(error_msg))

            timer = threading.Timer(timeout, _timeout_reject)
            timer.daemon = True
            timer.start()
            promise.set_metadata("_timeout_timer", timer)

            # Cancel the timer when the promise is settled
            def _cancel_timer(_: Any = None) -> None:
                if timer.is_alive():
                    timer.cancel()

            promise.then(lambda _: _cancel_timer(), lambda _: _cancel_timer())

        # Otherwise no timeout timer is needed

        logger.debug(
            f"Agent {self.agent_id} requested capability '{name}'"
            + (f" from provider {provider_id}" if provider_id else "")
            + (f" with timeout {timeout}" if timeout else "")
        )

        return promise

    def wait_for_capability(
        self, promise: Promise, wait_timeout: Optional[float] = None
    ) -> Any:
        """
        Wait for a capability request to be fulfilled.

        Args:
            promise: The promise returned from request_capability
            wait_timeout: Maximum time (in seconds) to wait, or None to use the promise's timeout

        Returns:
            The result of the capability execution

        Raises:
            TimeoutError: If the timeout is reached before the promise is fulfilled
            Exception: If the promise is rejected with an exception
        """
        # Use the provided wait_timeout, or fall back to the promise's metadata timeout
        effective_timeout = wait_timeout
        if effective_timeout is None:
            effective_timeout = promise.get_metadata("timeout")

        start_time = time.time()
        while promise.is_pending:
            # Check for timeout
            if (
                effective_timeout is not None
                and time.time() - start_time > effective_timeout
            ):
                error_msg = (
                    f"Capability request timed out after {effective_timeout} seconds"
                )
                promise.reject(TimeoutError(error_msg))
                raise TimeoutError(error_msg)

            # Small sleep to avoid busy waiting; tuned for test stability
            # Reduced from 0.1s to 0.02s to decrease flakiness in timer-based tests
            time.sleep(0.02)

        # Promise is no longer pending
        if promise.is_rejected:
            # Re-raise the exception
            raise promise.reason

        # Promise is fulfilled
        return promise.value

    def handle_pending_capabilities(self) -> int:
        """
        Process any pending capability requests for this agent.

        This method checks all capabilities this agent provides for any pending requests,
        and executes the appropriate handlers for each request.

        Returns:
            The number of capability requests handled
        """
        handled_count = 0

        # For each capability this agent provides
        for capability_name, capability_id in self._capability_ids.items():
            # Get the capability metadata from the broker
            capability = self.broker.get_capability(capability_id)
            if not capability:
                continue

            # Get the handler for this capability
            handler = self._capability_handlers.get(capability_name)
            if not handler:
                continue

            # For each active promise in this capability
            for promise_id, promise in list(capability.promises.items()):
                # Skip if the promise is already fulfilled or rejected
                if not promise.is_pending:
                    continue

                # Check for timeout
                timeout = promise.get_metadata("timeout")
                requested_at = promise.get_metadata("requested_at")
                if timeout is not None and requested_at is not None:
                    if time.time() - requested_at > timeout:
                        error_msg = f"Capability '{capability_name}' timed out after {timeout} seconds"
                        promise.reject(TimeoutError(error_msg))
                        continue

                # Extract arguments from promise metadata
                kwargs = {}
                for key, value in promise._metadata.items():
                    if key.startswith("arg_"):
                        arg_name = key[4:]  # Remove "arg_" prefix
                        kwargs[arg_name] = value

                # Execute the handler with the extracted arguments
                try:
                    handler.handle_request(promise, **kwargs)
                    handled_count += 1
                except Exception as e:
                    logger.error(
                        f"Error handling capability '{capability_name}' request: {e}"
                    )
                    promise.reject(e)

        return handled_count

    def get_available_capabilities(self) -> List[Dict[str, Any]]:
        """
        Get a list of capabilities available to this agent.

        Returns:
            List of capability metadata dictionaries
        """
        capabilities = self.broker.get_capabilities_available_to(self.agent_id)
        return [cap.to_dict() for cap in capabilities]

    def get_own_capabilities(self) -> List[Dict[str, Any]]:
        """
        Get a list of capabilities provided by this agent.

        Returns:
            List of capability metadata dictionaries
        """
        capabilities = self.broker.get_capabilities_provided_by(self.agent_id)
        return [cap.to_dict() for cap in capabilities]


class PromiseAgent:
    """
    Base class for agents that use the Promise system.

    This is a convenience class that inherits from PromiseAgentMixin
    and provides a standard agent implementation with Promise support.
    """

    def __init__(self, agent_id: str, broker: Optional[PromiseBroker] = None):
        """
        Initialize a Promise Agent.

        Args:
            agent_id: Unique identifier for this agent
            broker: PromiseBroker instance to use, or None to create a new one
        """
        # Initialize the mixin
        self.mixin = PromiseAgentMixin(agent_id, broker)

        # Expose mixin attributes and methods
        self.agent_id = self.mixin.agent_id
        self.broker = self.mixin.broker

    def register_capability(self, *args, **kwargs) -> str:
        """Delegate to mixin's register_capability."""
        return self.mixin.register_capability(*args, **kwargs)

    def unregister_capability(self, name: str) -> bool:
        """Delegate to mixin's unregister_capability."""
        return self.mixin.unregister_capability(name)

    def request_capability(self, *args, **kwargs) -> Promise:
        """Delegate to mixin's request_capability."""
        return self.mixin.request_capability(*args, **kwargs)

    def wait_for_capability(
        self, promise: Promise, wait_timeout: Optional[float] = None
    ) -> Any:
        """Delegate to mixin's wait_for_capability."""
        return self.mixin.wait_for_capability(promise, wait_timeout)

    def handle_pending_capabilities(self) -> int:
        """Delegate to mixin's handle_pending_capabilities."""
        return self.mixin.handle_pending_capabilities()

    def get_available_capabilities(self) -> List[Dict[str, Any]]:
        """Delegate to mixin's get_available_capabilities."""
        return self.mixin.get_available_capabilities()

    def get_own_capabilities(self) -> List[Dict[str, Any]]:
        """Delegate to mixin's get_own_capabilities."""
        return self.mixin.get_own_capabilities()

    def create_promise(
        self,
        type: "PromiseType",
        parameters: Dict[str, Any],
        context_id: str,
        tags: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
        priority: int = 1,
    ) -> Promise:
        """
        Create a new promise with the given parameters.

        Args:
            type: The type of capability being promised
            parameters: Specific parameters for this promise
            context_id: Context or task ID
            tags: Optional tags for filtering
            parent_id: Optional parent promise ID
            priority: Importance level (default 1)

        Returns:
            A newly created Promise in PENDING state
        """
        # Create a new Promise
        promise = Promise()

        # Set metadata
        promise.set_metadata("type", type)
        promise.set_metadata("parameters", parameters)
        promise.set_metadata("owner_id", self.agent_id)
        promise.set_metadata("context_id", context_id)
        if tags:
            promise.set_metadata("tags", tags)
        promise.set_metadata("priority", priority)

        # Set parent-child relationship if parent_id is provided
        if parent_id:
            promise.parent_id = parent_id
            promise.set_metadata("parent_id", parent_id)

            # Find the parent promise and add this promise as a child
            for p in self.mixin._pending_requests.values():
                if p.id == parent_id:
                    p.add_child_id(promise.id)
                    break

        # Track the promise locally so fulfillment and rejection handlers can
        # resolve it without requiring an explicit broker registration.
        self.mixin._pending_requests[promise.id] = promise

        return promise

    def fulfill_promise(self, promise_id: str, result: Any) -> None:
        """
        Fulfill a promise with the given result.

        Args:
            promise_id: ID of the promise to fulfill
            result: The result of the fulfilled promise

        Raises:
            ValueError: If the promise with the given ID is not found
        """
        # Find the promise in the pending requests
        for promise in self.mixin._pending_requests.values():
            if promise.id == promise_id:
                promise.resolve(result)
                return

        # Check if the promise is in the broker's capabilities
        for capability in self.broker.get_capabilities_provided_by(self.agent_id):
            for pid, promise in capability.promises.items():
                if promise.id == promise_id:
                    promise.resolve(result)
                    return

        # If we get here, the promise wasn't found
        raise ValueError(f"Promise with ID {promise_id} not found")

    def reject_promise(self, promise_id: str, reason: str) -> None:
        """
        Reject a promise with the given reason.

        Args:
            promise_id: ID of the promise to reject
            reason: The reason why the promise was rejected

        Raises:
            ValueError: If the promise with the given ID is not found
        """
        # Find the promise in the pending requests
        for promise in self.mixin._pending_requests.values():
            if promise.id == promise_id:
                promise.reject(Exception(reason))
                return

        # Check if the promise is in the broker's capabilities
        for capability in self.broker.get_capabilities_provided_by(self.agent_id):
            for pid, promise in capability.promises.items():
                if promise.id == promise_id:
                    promise.reject(Exception(reason))
                    return

        # If we get here, the promise wasn't found
        raise ValueError(f"Promise with ID {promise_id} not found")

    def create_child_promise(
        self,
        parent_id: str,
        type: "PromiseType",
        parameters: Dict[str, Any],
        context_id: str,
        tags: Optional[List[str]] = None,
        priority: int = 1,
    ) -> Promise:
        """
        Create a child promise linked to a parent promise.

        Args:
            parent_id: ID of the parent promise
            type: Type of capability
            parameters: Parameters for this promise
            context_id: Context or task ID
            tags: Optional tags
            priority: Importance level

        Returns:
            A newly created Promise linked to its parent
        """
        # Find the parent promise first to verify it exists
        parent_promise = None
        for promise in self.mixin._pending_requests.values():
            if promise.id == parent_id:
                parent_promise = promise
                break

        if parent_promise is None:
            raise ValueError(f"Parent promise with ID {parent_id} not found")

        # Create a new Promise
        child_promise = self.create_promise(
            type=type,
            parameters=parameters,
            context_id=context_id,
            tags=tags,
            parent_id=parent_id,
            priority=priority,
        )

        # Ensure the parent-child relationship is established
        parent_promise.add_child_id(child_promise.id)

        return child_promise

    def run(self) -> None:
        """
        Run the agent's main loop.

        This method should be overridden by subclasses to implement
        the agent's specific behavior. The default implementation
        simply handles pending capability requests.
        """
        self.handle_pending_capabilities()
