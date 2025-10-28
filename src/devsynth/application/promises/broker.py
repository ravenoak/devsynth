"""
Promise Broker implementation for DevSynth.

The Promise Broker serves as a central registry for capabilities provided by different
agents within the DevSynth system. It handles capability registration, discovery,
request matching, and authorization.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from devsynth.exceptions import DevSynthError

from .implementation import Promise, PromiseError

# Setup logger
logger = logging.getLogger(__name__)


class PromiseBrokerError(PromiseError):
    """Base class for Promise Broker errors."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Promise broker error")


class CapabilityNotFoundError(PromiseBrokerError):
    """Error raised when a requested capability is not found."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Capability not found")


class UnauthorizedAccessError(PromiseBrokerError):
    """Error raised when an agent attempts to access a capability it's not authorized for."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Unauthorized access")


class CapabilityAlreadyRegisteredError(PromiseBrokerError):
    """Error raised when attempting to register a capability that's already registered."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Capability already registered")


class CapabilityMetadata:
    """Metadata for a registered capability."""

    def __init__(
        self,
        name: str,
        description: str,
        provider_id: str,
        parameters: dict[str, str] = None,
        tags: list[str] = None,
        authorized_requesters: set[str] = None,
    ):
        """
        Initialize capability metadata.

        Args:
            name: The name of the capability
            description: A description of what the capability does
            provider_id: The ID of the agent providing this capability
            parameters: A dictionary mapping parameter names to their types
            tags: A list of tags for categorizing the capability
            authorized_requesters: Set of agent IDs that are authorized to use this capability.
                If None, all agents are authorized.
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.provider_id = provider_id
        self.parameters = parameters or {}
        self.tags = tags or []
        self.authorized_requesters = authorized_requesters
        self.promises: dict[str, Promise] = {}

    def authorize(self, requester_id: str) -> bool:
        """
        Check if a requester is authorized to use this capability.

        Args:
            requester_id: The ID of the agent requesting the capability

        Returns:
            True if authorized, False otherwise
        """
        # If no authorized_requesters are specified, all agents are authorized
        if self.authorized_requesters is None:
            return True

        # Check if the requester is in the authorized set
        return requester_id in self.authorized_requesters

    def add_promise(self, promise_id: str, promise: Promise) -> None:
        """
        Associate a promise with this capability.

        Args:
            promise_id: Unique identifier for the promise
            promise: The promise object
        """
        self.promises[promise_id] = promise

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the capability metadata to a dictionary.

        Returns:
            Dictionary representation of the capability metadata
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "provider_id": self.provider_id,
            "parameters": self.parameters,
            "tags": self.tags,
            "authorized_requesters": (
                list(self.authorized_requesters) if self.authorized_requesters else None
            ),
            "active_promises": len(self.promises),
        }


class PromiseBroker:
    """
    Central manager for capability registration, discovery, and fulfillment.

    The Promise Broker:
    1. Maintains a registry of capabilities provided by agents
    2. Matches capability requests with providers
    3. Enforces access control for capabilities
    4. Tracks capability usage and promise chains
    """

    def __init__(self):
        """Initialize the Promise Broker."""
        # Map of capability ID to capability metadata
        self._capabilities: dict[str, CapabilityMetadata] = {}

        # Map of capability name to list of capability IDs (for lookup by name)
        self._capability_name_index: dict[str, list[str]] = {}

        # Map of provider ID to list of capability IDs (for lookup by provider)
        self._provider_index: dict[str, list[str]] = {}

        # Map of tag to list of capability IDs (for lookup by tag)
        self._tag_index: dict[str, list[str]] = {}

        logger.debug("Promise Broker initialized")

    def register_capability(
        self,
        name: str,
        description: str,
        provider_id: str,
        parameters: dict[str, str] = None,
        tags: list[str] = None,
        authorized_requesters: set[str] = None,
    ) -> str:
        """
        Register a new capability with the broker.

        Args:
            name: The name of the capability
            description: A description of what the capability does
            provider_id: The ID of the agent providing this capability
            parameters: A dictionary mapping parameter names to their types
            tags: A list of tags for categorizing the capability
            authorized_requesters: Set of agent IDs that are authorized to use this capability.
                If None, all agents are authorized.

        Returns:
            The ID of the registered capability

        Raises:
            CapabilityAlreadyRegisteredError: If a capability with the same name and provider exists
        """
        # Create capability metadata
        capability = CapabilityMetadata(
            name=name,
            description=description,
            provider_id=provider_id,
            parameters=parameters,
            tags=tags,
            authorized_requesters=authorized_requesters,
        )

        # Check if a capability with the same name and provider already exists
        if name in self._capability_name_index:
            for cap_id in self._capability_name_index[name]:
                if self._capabilities[cap_id].provider_id == provider_id:
                    raise CapabilityAlreadyRegisteredError(
                        f"Capability '{name}' is already registered by provider '{provider_id}'"
                    )

        # Store the capability
        self._capabilities[capability.id] = capability

        # Update the name index
        if name not in self._capability_name_index:
            self._capability_name_index[name] = []
        self._capability_name_index[name].append(capability.id)

        # Update the provider index
        if provider_id not in self._provider_index:
            self._provider_index[provider_id] = []
        self._provider_index[provider_id].append(capability.id)

        # Update the tag index
        if tags:
            for tag in tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                self._tag_index[tag].append(capability.id)

        logger.debug(
            f"Registered capability '{name}' with ID {capability.id} from provider {provider_id}"
        )
        return capability.id

    def unregister_capability(self, capability_id: str) -> bool:
        """
        Unregister a capability from the broker.

        Args:
            capability_id: The ID of the capability to unregister

        Returns:
            True if the capability was unregistered, False if it wasn't found
        """
        if capability_id not in self._capabilities:
            return False

        capability = self._capabilities[capability_id]

        # Remove from capability index
        del self._capabilities[capability_id]

        # Remove from name index
        self._capability_name_index[capability.name].remove(capability_id)
        if not self._capability_name_index[capability.name]:
            del self._capability_name_index[capability.name]

        # Remove from provider index
        self._provider_index[capability.provider_id].remove(capability_id)
        if not self._provider_index[capability.provider_id]:
            del self._provider_index[capability.provider_id]

        # Remove from tag index
        for tag in capability.tags:
            if tag in self._tag_index:
                self._tag_index[tag].remove(capability_id)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]

        logger.debug(f"Unregistered capability {capability_id} ('{capability.name}')")
        return True

    def get_capability(self, capability_id: str) -> CapabilityMetadata | None:
        """
        Get metadata for a specific capability.

        Args:
            capability_id: The ID of the capability to retrieve

        Returns:
            The capability metadata, or None if not found
        """
        return self._capabilities.get(capability_id)

    def find_capabilities(
        self,
        name: str | None = None,
        provider_id: str | None = None,
        tags: list[str] | None = None,
        requester_id: str | None = None,
    ) -> list[CapabilityMetadata]:
        """
        Find capabilities matching the given criteria.

        Args:
            name: Filter by capability name
            provider_id: Filter by provider ID
            tags: Filter by tags (capabilities must have ALL specified tags)
            requester_id: If provided, only return capabilities the requester is authorized to use

        Returns:
            List of matching capability metadata objects
        """
        # Start with all capability IDs
        candidate_ids: set[str] = set(self._capabilities.keys())

        # Filter by name
        if name is not None:
            if name in self._capability_name_index:
                candidate_ids &= set(self._capability_name_index[name])
            else:
                return []  # No capabilities with this name

        # Filter by provider
        if provider_id is not None:
            if provider_id in self._provider_index:
                candidate_ids &= set(self._provider_index[provider_id])
            else:
                return []  # No capabilities from this provider

        # Filter by tags (must have ALL specified tags)
        if tags:
            for tag in tags:
                if tag in self._tag_index:
                    candidate_ids &= set(self._tag_index[tag])
                else:
                    return []  # No capabilities with this tag

        # Convert IDs to capability metadata objects
        candidates = [self._capabilities[cap_id] for cap_id in candidate_ids]

        # Filter by authorization if a requester_id is provided
        if requester_id is not None:
            candidates = [cap for cap in candidates if cap.authorize(requester_id)]

        return candidates

    def request_capability(
        self,
        requester_id: str,
        name: str,
        provider_id: str | None = None,
        tags: list[str] | None = None,
    ) -> Promise:
        """
        Request a capability from the broker.

        Args:
            requester_id: The ID of the agent requesting the capability
            name: The name of the requested capability
            provider_id: Optional provider ID to request from a specific provider
            tags: Optional tags to filter capabilities

        Returns:
            A Promise that will be fulfilled when the capability is exercised

        Raises:
            CapabilityNotFoundError: If no matching capability is found
            UnauthorizedAccessError: If the requester is not authorized to use the capability
        """
        # Find matching capabilities
        candidates = self.find_capabilities(
            name=name, provider_id=provider_id, tags=tags
        )

        if not candidates:
            raise CapabilityNotFoundError(
                f"No capability found with name '{name}'"
                + (f" from provider '{provider_id}'" if provider_id else "")
                + (f" with tags {tags}" if tags else "")
            )

        # Choose the most appropriate capability (currently just the first one)
        capability = candidates[0]

        # Check authorization
        if not capability.authorize(requester_id):
            raise UnauthorizedAccessError(
                f"Agent '{requester_id}' is not authorized to use capability '{capability.name}' "
                f"from provider '{capability.provider_id}'"
            )

        # Create a promise for this capability request
        promise = Promise[Any]()
        promise_id = str(uuid.uuid4())

        # Store the promise in the capability metadata
        capability.add_promise(promise_id, promise)

        # Add metadata to the promise for tracing
        promise.set_metadata("capability_id", capability.id)
        promise.set_metadata("capability_name", capability.name)
        promise.set_metadata("provider_id", capability.provider_id)
        promise.set_metadata("requester_id", requester_id)
        promise.set_metadata("promise_id", promise_id)

        logger.debug(
            f"Created promise {promise_id} for capability '{capability.name}' "
            f"requested by '{requester_id}' from provider '{capability.provider_id}'"
        )

        return promise

    def get_capabilities_provided_by(
        self, provider_id: str
    ) -> list[CapabilityMetadata]:
        """
        Get all capabilities provided by a specific agent.

        Args:
            provider_id: The ID of the provider agent

        Returns:
            List of capability metadata objects
        """
        if provider_id not in self._provider_index:
            return []

        return [
            self._capabilities[cap_id] for cap_id in self._provider_index[provider_id]
        ]

    def get_capabilities_available_to(
        self, requester_id: str
    ) -> list[CapabilityMetadata]:
        """
        Get all capabilities available to a specific agent.

        Args:
            requester_id: The ID of the potential requester

        Returns:
            List of capability metadata objects the requester is authorized to use
        """
        return [
            cap for cap in self._capabilities.values() if cap.authorize(requester_id)
        ]

    def register_capability_with_type(
        self, agent_id: str, promise_type, constraints: dict[str, Any]
    ) -> str:
        """
        Register a capability for an agent with the given promise type and constraints.

        This is a convenience method that wraps the standard register_capability method
        with a simplified interface for use in tests and other contexts.

        Args:
            agent_id: The ID of the agent providing this capability
            promise_type: The type of capability being registered
            constraints: Constraints on the capability parameters

        Returns:
            The ID of the registered capability
        """
        return self.register_capability(
            name=promise_type.name,
            description=f"Capability for {promise_type.name}",
            provider_id=agent_id,
            parameters=constraints,
            tags=[promise_type.name],
        )
