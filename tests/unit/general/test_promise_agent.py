"""
Unit tests for the Promise Agent integration.
"""

import time
from typing import Any, Dict, List

import pytest

from devsynth.application.promises import (
    CapabilityHandler,
    CapabilityNotFoundError,
    Promise,
    PromiseAgent,
    PromiseAgentMixin,
    PromiseBroker,
    UnauthorizedAccessError,
)


class TestCapabilityHandler:
    """Test suite for the CapabilityHandler class.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_handler_initialization_succeeds(self):
        """Test initializing a capability handler.

        ReqID: N/A"""

        def add_numbers(a: int, b: int) -> int:
            return a + b

        handler = CapabilityHandler(
            agent_id="test_agent",
            capability_name="add_numbers",
            handler_func=add_numbers,
            description="Add two numbers together",
            parameters={"a": "int", "b": "int"},
            tags=["math", "addition"],
        )
        assert handler.agent_id == "test_agent"
        assert handler.capability_name == "add_numbers"
        assert handler.handler_func is add_numbers
        assert handler.description == "Add two numbers together"
        assert handler.parameters == {"a": "int", "b": "int"}
        assert handler.tags == ["math", "addition"]
        assert handler._active_promises == {}

    @pytest.mark.fast
    def test_handler_direct_execution_succeeds(self):
        """Test direct execution of a handler.

        ReqID: N/A"""

        def multiply_numbers(a: int, b: int) -> int:
            return a * b

        handler = CapabilityHandler(
            agent_id="test_agent",
            capability_name="multiply_numbers",
            handler_func=multiply_numbers,
            description="Multiply two numbers together",
            parameters={"a": "int", "b": "int"},
        )
        result = handler(3, 4)
        assert result == 12

    @pytest.mark.fast
    def test_handler_promise_execution_succeeds(self):
        """Test executing a handler through a promise.

        ReqID: N/A"""

        def subtract_numbers(a: int, b: int) -> int:
            return a - b

        handler = CapabilityHandler(
            agent_id="test_agent",
            capability_name="subtract_numbers",
            handler_func=subtract_numbers,
            description="Subtract two numbers",
            parameters={"a": "int", "b": "int"},
        )
        promise = Promise[int]()
        handler.handle_request(promise, a=10, b=3)
        assert promise.is_fulfilled
        assert promise.value == 7
        assert "execution_started_at" in promise._metadata
        assert "execution_completed_at" in promise._metadata
        assert len(handler._active_promises) == 0

    @pytest.mark.fast
    def test_handler_promise_error_raises_error(self):
        """Test error handling in a capability handler.

        ReqID: N/A"""

        def divide_numbers(a: int, b: int) -> float:
            if b == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            return a / b

        handler = CapabilityHandler(
            agent_id="test_agent",
            capability_name="divide_numbers",
            handler_func=divide_numbers,
            description="Divide two numbers",
            parameters={"a": "int", "b": "int"},
        )
        promise = Promise[float]()
        handler.handle_request(promise, a=10, b=0)
        assert promise.is_rejected
        assert isinstance(promise.reason, ZeroDivisionError)
        assert str(promise.reason) == "Cannot divide by zero"
        assert "execution_started_at" in promise._metadata
        assert "execution_failed_at" in promise._metadata
        assert "error_message" in promise._metadata
        assert len(handler._active_promises) == 0


class TestPromiseAgent:
    """Test suite for the PromiseAgent class.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_agent_initialization_succeeds(self):
        """Test initializing a promise agent.

        ReqID: N/A"""
        broker = PromiseBroker()
        agent = PromiseAgent(agent_id="test_agent", broker=broker)
        assert agent.agent_id == "test_agent"
        assert agent.broker is broker

    @pytest.mark.fast
    def test_capability_registration_succeeds(self):
        """Test registering a capability with an agent.

        ReqID: N/A"""
        agent = PromiseAgent(agent_id="provider_agent")

        def add_numbers(a: int, b: int) -> int:
            return a + b

        capability_id = agent.register_capability(
            name="add",
            handler_func=add_numbers,
            description="Add two numbers together",
            parameters={"a": "int", "b": "int"},
            tags=["math", "basic"],
        )
        assert capability_id is not None
        capabilities = agent.get_own_capabilities()
        assert len(capabilities) == 1
        assert capabilities[0]["name"] == "add"
        assert capabilities[0]["provider_id"] == "provider_agent"

    @pytest.mark.fast
    def test_capability_request_and_fulfillment_succeeds(self):
        """Test requesting and fulfilling a capability.

        ReqID: N/A"""
        broker = PromiseBroker()
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)

        def multiply_numbers(a: int, b: int) -> int:
            return a * b

        provider.register_capability(
            name="multiply",
            handler_func=multiply_numbers,
            description="Multiply two numbers together",
            parameters={"a": "int", "b": "int"},
        )
        requester = PromiseAgent(agent_id="requester_agent", broker=broker)
        promise = requester.request_capability(name="multiply", a=5, b=7)
        provider.handle_pending_capabilities()
        assert promise.is_fulfilled
        assert promise.value == 35

    @pytest.mark.medium
    def test_capability_request_with_timeout_succeeds(self):
        """Test requesting a capability with a timeout.

        Speed: medium because it relies on a timer-based timeout and a short sleep to ensure the timer fires deterministically.
        ReqID: N/A"""
        broker = PromiseBroker()
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)

        def slow_operation(delay: float) -> str:
            time.sleep(delay)
            return "Completed"

        provider.register_capability(
            name="slow_operation",
            handler_func=slow_operation,
            description="A slow operation",
            parameters={"delay": "float"},
        )
        requester = PromiseAgent(agent_id="requester_agent", broker=broker)
        promise = requester.request_capability(
            name="slow_operation", timeout=0.05, delay=1
        )
        # Poll for rejection to avoid long sleeps and reduce wall time
        deadline = time.perf_counter() + 0.5
        while not promise.is_rejected and time.perf_counter() < deadline:
            time.sleep(0.005)
        provider.handle_pending_capabilities()
        assert promise.is_rejected
        assert isinstance(promise.reason, TimeoutError)

    @pytest.mark.medium
    def test_wait_for_capability_succeeds(self):
        """Test waiting for a capability to complete.

        Speed: medium because it spawns a background thread and waits for inter-thread coordination with a short sleep.
        ReqID: N/A"""
        broker = PromiseBroker()
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)

        def greet(person_name: str) -> str:
            return f"Hello, {person_name}!"

        provider.register_capability(
            name="greet",
            handler_func=greet,
            description="Greet a person",
            parameters={"person_name": "str"},
        )
        requester = PromiseAgent(agent_id="requester_agent", broker=broker)
        promise = requester.request_capability(name="greet", person_name="World")

        def process_later():
            time.sleep(0.05)
            provider.handle_pending_capabilities()

        import threading

        thread = threading.Thread(target=process_later)
        thread.start()
        result = requester.wait_for_capability(promise)
        assert result == "Hello, World!"
        thread.join()

    @pytest.mark.fast
    def test_unauthorized_access_succeeds(self):
        """Test unauthorized access to a capability.

        ReqID: N/A"""
        broker = PromiseBroker()
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)

        def secret_operation() -> str:
            return "Secret information"

        provider.register_capability(
            name="secret_operation",
            handler_func=secret_operation,
            description="A restricted operation",
            authorized_requesters={"authorized_agent"},
        )
        unauthorized = PromiseAgent(agent_id="unauthorized_agent", broker=broker)
        with pytest.raises(UnauthorizedAccessError):
            unauthorized.request_capability(name="secret_operation")

    @pytest.mark.fast
    def test_capability_not_found_succeeds(self):
        """Test requesting a non-existent capability.

        ReqID: N/A"""
        requester = PromiseAgent(agent_id="requester_agent")
        with pytest.raises(CapabilityNotFoundError):
            requester.request_capability(name="non_existent_capability")

    @pytest.mark.fast
    def test_get_available_capabilities_succeeds(self):
        """Test getting available capabilities.

        ReqID: N/A"""
        broker = PromiseBroker()
        provider = PromiseAgent(agent_id="provider_agent", broker=broker)
        provider.register_capability(
            name="capability1",
            handler_func=lambda: "result1",
            description="Capability 1",
        )
        provider.register_capability(
            name="capability2",
            handler_func=lambda: "result2",
            description="Capability 2",
            tags=["tag1", "tag2"],
        )
        provider.register_capability(
            name="restricted",
            handler_func=lambda: "restricted",
            description="Restricted capability",
            authorized_requesters={"other_agent"},
        )
        requester = PromiseAgent(agent_id="requester_agent", broker=broker)
        capabilities = requester.get_available_capabilities()
        assert len(capabilities) == 2
        capabilities.sort(key=lambda c: c["name"])
        assert capabilities[0]["name"] == "capability1"
        assert capabilities[0]["provider_id"] == "provider_agent"
        assert capabilities[1]["name"] == "capability2"
        assert capabilities[1]["provider_id"] == "provider_agent"
        assert set(capabilities[1]["tags"]) == {"tag1", "tag2"}


class TestPromiseAgentMixin:
    """Test suite for the PromiseAgentMixin class.

    ReqID: N/A"""

    class CustomAgent:
        """A custom agent class that uses the PromiseAgentMixin."""

        def __init__(self, agent_id: str, broker: PromiseBroker = None):
            self.promise_agent = PromiseAgentMixin(agent_id, broker)
            self.custom_state = "initialized"

        def do_custom_action(self) -> str:
            self.custom_state = "action_performed"
            return "Custom action performed"

    @pytest.mark.fast
    def test_mixin_with_custom_agent_succeeds(self):
        """Test using the PromiseAgentMixin with a custom agent class.

        ReqID: N/A"""
        agent = self.CustomAgent(agent_id="custom_agent")
        assert agent.promise_agent.agent_id == "custom_agent"
        assert agent.custom_state == "initialized"
        result = agent.do_custom_action()
        assert result == "Custom action performed"
        assert agent.custom_state == "action_performed"

        def example_capability(x: int) -> int:
            return x * 2

        capability_id = agent.promise_agent.register_capability(
            name="example",
            handler_func=example_capability,
            description="An example capability",
            parameters={"x": "int"},
        )
        assert capability_id is not None
        capabilities = agent.promise_agent.get_own_capabilities()
        assert len(capabilities) == 1
        assert capabilities[0]["name"] == "example"
