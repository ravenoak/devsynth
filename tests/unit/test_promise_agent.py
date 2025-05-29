"""
Unit tests for the Promise Agent integration.
"""
import pytest
import time
from typing import Dict, Any, List

from devsynth.application.promises import (
    Promise, PromiseBroker, PromiseAgent, PromiseAgentMixin,
    CapabilityHandler, CapabilityNotFoundError, UnauthorizedAccessError
)


class TestCapabilityHandler:
    """Test suite for the CapabilityHandler class."""

    def test_handler_initialization(self):
        """Test initializing a capability handler."""
        # Create a simple handler function
        def add_numbers(a: int, b: int) -> int:
            return a + b

        # Create a handler
        handler = CapabilityHandler(
            agent_id="test_agent",
            capability_name="add_numbers",
            handler_func=add_numbers,
            description="Add two numbers together",
            parameters={"a": "int", "b": "int"},
            tags=["math", "addition"]
        )

        # Verify the handler's properties
        assert handler.agent_id == "test_agent"
        assert handler.capability_name == "add_numbers"
        assert handler.handler_func is add_numbers
        assert handler.description == "Add two numbers together"
        assert handler.parameters == {"a": "int", "b": "int"}
        assert handler.tags == ["math", "addition"]
        assert handler._active_promises == {}

    def test_handler_direct_execution(self):
        """Test direct execution of a handler."""
        # Create a simple handler function
        def multiply_numbers(a: int, b: int) -> int:
            return a * b

        # Create a handler
        handler = CapabilityHandler(
            agent_id="test_agent",
            capability_name="multiply_numbers",
            handler_func=multiply_numbers,
            description="Multiply two numbers together",
            parameters={"a": "int", "b": "int"}
        )

        # Execute the handler directly
        result = handler(3, 4)
        assert result == 12

    def test_handler_promise_execution(self):
        """Test executing a handler through a promise."""
        # Create a simple handler function
        def subtract_numbers(a: int, b: int) -> int:
            return a - b

        # Create a handler
        handler = CapabilityHandler(
            agent_id="test_agent",
            capability_name="subtract_numbers",
            handler_func=subtract_numbers,
            description="Subtract two numbers",
            parameters={"a": "int", "b": "int"}
        )

        # Create a promise
        promise = Promise[int]()

        # Handle a request using the promise
        handler.handle_request(promise, a=10, b=3)

        # Verify the promise was resolved correctly
        assert promise.is_fulfilled
        assert promise.value == 7
        assert "execution_started_at" in promise._metadata
        assert "execution_completed_at" in promise._metadata

        # Verify the promise was removed from active promises
        assert len(handler._active_promises) == 0

    def test_handler_promise_error(self):
        """Test error handling in a capability handler."""
        # Create a handler function that raises an exception
        def divide_numbers(a: int, b: int) -> float:
            if b == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            return a / b

        # Create a handler
        handler = CapabilityHandler(
            agent_id="test_agent",
            capability_name="divide_numbers",
            handler_func=divide_numbers,
            description="Divide two numbers",
            parameters={"a": "int", "b": "int"}
        )

        # Create a promise
        promise = Promise[float]()

        # Handle a request that will cause an error
        handler.handle_request(promise, a=10, b=0)

        # Verify the promise was rejected correctly
        assert promise.is_rejected
        assert isinstance(promise.reason, ZeroDivisionError)
        assert str(promise.reason) == "Cannot divide by zero"
        assert "execution_started_at" in promise._metadata
        assert "execution_failed_at" in promise._metadata
        assert "error_message" in promise._metadata

        # Verify the promise was removed from active promises
        assert len(handler._active_promises) == 0


class TestPromiseAgent:
    """Test suite for the PromiseAgent class."""

    def test_agent_initialization(self):
        """Test initializing a promise agent."""
        # Create a broker
        broker = PromiseBroker()

        # Create an agent
        agent = PromiseAgent(agent_id="test_agent", broker=broker)

        # Verify the agent's properties
        assert agent.agent_id == "test_agent"
        assert agent.broker is broker

    def test_capability_registration(self):
        """Test registering a capability with an agent."""
        # Create an agent
        agent = PromiseAgent(agent_id="provider_agent")

        # Define a capability function
        def add_numbers(a: int, b: int) -> int:
            return a + b

        # Register the capability
        capability_id = agent.register_capability(
            name="add",
            handler_func=add_numbers,
            description="Add two numbers together",
            parameters={"a": "int", "b": "int"},
            tags=["math", "basic"]
        )

        # Verify the capability was registered
        assert capability_id is not None

        # Check if the capability is available
        capabilities = agent.get_own_capabilities()
        assert len(capabilities) == 1
        assert capabilities[0]["name"] == "add"
        assert capabilities[0]["provider_id"] == "provider_agent"

    def test_capability_request_and_fulfillment(self):
        """Test requesting and fulfilling a capability."""
        # Create a broker to share between agents
        broker = PromiseBroker()

        # Create a provider agent
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)

        # Define a capability function
        def multiply_numbers(a: int, b: int) -> int:
            return a * b

        # Register the capability
        provider.register_capability(
            name="multiply",
            handler_func=multiply_numbers,
            description="Multiply two numbers together",
            parameters={"a": "int", "b": "int"}
        )

        # Create a requester agent
        requester = PromiseAgent(agent_id="requester_agent", broker=broker)

        # Request the capability
        promise = requester.request_capability(
            name="multiply",
            a=5,
            b=7
        )

        # Process pending capability requests
        provider.handle_pending_capabilities()

        # Verify the promise was fulfilled
        assert promise.is_fulfilled
        assert promise.value == 35

    def test_capability_request_with_timeout(self):
        """Test requesting a capability with a timeout."""
        # Create a broker to share between agents
        broker = PromiseBroker()

        # Create a provider agent
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)

        # Define a capability function that takes time
        def slow_operation(delay: float) -> str:
            time.sleep(delay)
            return "Completed"

        # Register the capability
        provider.register_capability(
            name="slow_operation",
            handler_func=slow_operation,
            description="A slow operation",
            parameters={"delay": "float"}
        )

        # Create a requester agent
        requester = PromiseAgent(agent_id="requester_agent", broker=broker)

        # Request the capability with a short timeout
        promise = requester.request_capability(
            name="slow_operation",
            timeout=0.5,  # 500ms timeout
            delay=2  # 2 second operation
        )

        # Wait for the timeout to expire
        time.sleep(0.6)

        # Process pending capability requests (should reject due to timeout)
        provider.handle_pending_capabilities()

        # Verify the promise was rejected with a timeout error
        assert promise.is_rejected
        assert isinstance(promise.reason, TimeoutError)

    def test_wait_for_capability(self):
        """Test waiting for a capability to complete."""
        # Create a broker to share between agents
        broker = PromiseBroker()

        # Create a provider agent
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)

        # Define a capability function
        def greet(person_name: str) -> str:
            return f"Hello, {person_name}!"

        # Register the capability
        provider.register_capability(
            name="greet",
            handler_func=greet,
            description="Greet a person",
            parameters={"person_name": "str"}
        )

        # Create a requester agent
        requester = PromiseAgent(agent_id="requester_agent", broker=broker)

        # Request the capability
        promise = requester.request_capability(
            name="greet",
            person_name="World"
        )

        # Process pending capability requests in a separate thread to simulate asynchronous handling
        def process_later():
            time.sleep(0.5)  # Delay to simulate asynchronous processing
            provider.handle_pending_capabilities()

        import threading
        thread = threading.Thread(target=process_later)
        thread.start()

        # Wait for the capability to complete
        result = requester.wait_for_capability(promise)

        # Verify the result
        assert result == "Hello, World!"
        thread.join()  # Clean up the thread

    def test_unauthorized_access(self):
        """Test unauthorized access to a capability."""
        # Create a broker to share between agents
        broker = PromiseBroker()

        # Create a provider agent
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)

        # Define a capability function
        def secret_operation() -> str:
            return "Secret information"

        # Register the capability with authorization
        provider.register_capability(
            name="secret_operation",
            handler_func=secret_operation,
            description="A restricted operation",
            authorized_requesters={"authorized_agent"}  # Only this agent is authorized
        )

        # Create an unauthorized requester agent
        unauthorized = PromiseAgent(agent_id="unauthorized_agent", broker=broker)

        # Request the capability
        with pytest.raises(UnauthorizedAccessError):
            unauthorized.request_capability(name="secret_operation")

    def test_capability_not_found(self):
        """Test requesting a non-existent capability."""
        # Create a requester agent
        requester = PromiseAgent(agent_id="requester_agent")

        # Request a non-existent capability
        with pytest.raises(CapabilityNotFoundError):
            requester.request_capability(name="non_existent_capability")

    def test_get_available_capabilities(self):
        """Test getting available capabilities."""
        # Create a broker to share between agents
        broker = PromiseBroker()

        # Create a provider agent
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)

        # Register multiple capabilities
        provider.register_capability(
            name="capability1",
            handler_func=lambda: "result1",
            description="Capability 1"
        )

        provider.register_capability(
            name="capability2",
            handler_func=lambda: "result2",
            description="Capability 2",
            tags=["tag1", "tag2"]
        )

        provider.register_capability(
            name="restricted",
            handler_func=lambda: "restricted",
            description="Restricted capability",
            authorized_requesters={"other_agent"}
        )

        # Create a requester agent
        requester = PromiseAgent(agent_id="requester_agent", broker=broker)

        # Get available capabilities
        capabilities = requester.get_available_capabilities()

        # Verify the available capabilities
        assert len(capabilities) == 2  # Should not include the restricted capability

        # Sort capabilities by name for consistent testing
        capabilities.sort(key=lambda c: c["name"])

        assert capabilities[0]["name"] == "capability1"
        assert capabilities[0]["provider_id"] == "provider_agent"

        assert capabilities[1]["name"] == "capability2"
        assert capabilities[1]["provider_id"] == "provider_agent"
        assert set(capabilities[1]["tags"]) == {"tag1", "tag2"}


class TestPromiseAgentMixin:
    """Test suite for the PromiseAgentMixin class."""

    class CustomAgent:
        """A custom agent class that uses the PromiseAgentMixin."""

        def __init__(self, agent_id: str, broker: PromiseBroker = None):
            self.promise_agent = PromiseAgentMixin(agent_id, broker)
            self.custom_state = "initialized"

        def do_custom_action(self) -> str:
            self.custom_state = "action_performed"
            return "Custom action performed"

    def test_mixin_with_custom_agent(self):
        """Test using the PromiseAgentMixin with a custom agent class."""
        # Create a custom agent
        agent = self.CustomAgent(agent_id="custom_agent")

        # Verify the agent's properties
        assert agent.promise_agent.agent_id == "custom_agent"
        assert agent.custom_state == "initialized"

        # Perform a custom action
        result = agent.do_custom_action()
        assert result == "Custom action performed"
        assert agent.custom_state == "action_performed"

        # Use the mixin to register a capability
        def example_capability(x: int) -> int:
            return x * 2

        capability_id = agent.promise_agent.register_capability(
            name="example",
            handler_func=example_capability,
            description="An example capability",
            parameters={"x": "int"}
        )

        # Verify the capability was registered
        assert capability_id is not None

        # Use the mixin to check own capabilities
        capabilities = agent.promise_agent.get_own_capabilities()
        assert len(capabilities) == 1
        assert capabilities[0]["name"] == "example"
