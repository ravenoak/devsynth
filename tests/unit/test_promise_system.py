"""
Unit tests for the Promise system.
"""
import pytest
from typing import List, Any, Optional

from devsynth.application.promises import Promise, PromiseState, PromiseError, PromiseStateError


class TestPromise:
    """Test suite for the Promise class."""

    def test_initial_state(self):
        """Test the initial state of a Promise."""
        promise = Promise()
        assert promise.state == PromiseState.PENDING
        assert promise.is_pending
        assert not promise.is_fulfilled
        assert not promise.is_rejected

    def test_resolve(self):
        """Test resolving a Promise."""
        promise = Promise[str]()
        promise.resolve("test value")

        assert promise.state == PromiseState.FULFILLED
        assert promise.is_fulfilled
        assert not promise.is_pending
        assert promise.value == "test value"

        # Cannot resolve again
        with pytest.raises(PromiseStateError):
            promise.resolve("another value")

    def test_reject(self):
        """Test rejecting a Promise."""
        promise = Promise()
        error = ValueError("test error")
        promise.reject(error)

        assert promise.state == PromiseState.REJECTED
        assert promise.is_rejected
        assert not promise.is_pending
        assert promise.reason is error

        # Cannot reject again
        with pytest.raises(PromiseStateError):
            promise.reject(Exception("another error"))

    def test_then_fulfilled(self):
        """Test the 'then' method with a fulfilled Promise."""
        initial_promise = Promise[int]()
        initial_promise.resolve(42)

        result = []

        def on_fulfilled(value):
            result.append(value * 2)
            return value * 2

        def on_rejected(reason):
            result.append(f"Error: {reason}")
            return None

        next_promise = initial_promise.then(on_fulfilled, on_rejected)

        assert result == [84]
        assert next_promise.is_fulfilled
        assert next_promise.value == 84

    def test_then_rejected(self):
        """Test the 'then' method with a rejected Promise."""
        initial_promise = Promise()
        error = ValueError("test error")
        initial_promise.reject(error)

        result = []

        def on_fulfilled(value):
            result.append(value)
            return value

        def on_rejected(reason):
            result.append(f"Error: {reason}")
            return "handled"

        next_promise = initial_promise.then(on_fulfilled, on_rejected)

        assert result == [f"Error: {error}"]
        assert next_promise.is_fulfilled
        assert next_promise.value == "handled"

    def test_catch(self):
        """Test the 'catch' method."""
        initial_promise = Promise()
        error = ValueError("test error")
        initial_promise.reject(error)

        result = []

        def on_rejected(reason):
            result.append(f"Caught: {reason}")
            return "recovered"

        next_promise = initial_promise.catch(on_rejected)

        assert result == [f"Caught: {error}"]
        assert next_promise.is_fulfilled
        assert next_promise.value == "recovered"

    def test_chaining(self):
        """Test chaining multiple promises."""
        initial_promise = Promise[int]()

        def double(x: int) -> int:
            return x * 2

        def add_ten(x: int) -> int:
            return x + 10

        def stringify(x: int) -> str:
            return f"Result: {x}"

        final_promise = (
            initial_promise
            .then(double)
            .then(add_ten)
            .then(stringify)
        )

        initial_promise.resolve(5)

        assert final_promise.is_fulfilled
        assert final_promise.value == "Result: 20"

    def test_error_propagation(self):
        """Test error propagation through chains."""
        initial_promise = Promise[int]()

        def double(x: int) -> int:
            return x * 2

        def will_fail(x: int) -> int:
            raise ValueError(f"Failed on {x}")

        def add_ten(x: int) -> int:
            return x + 10

        def handle_error(e: Exception) -> str:
            return f"Handled: {e}"

        final_promise = (
            initial_promise
            .then(double)
            .then(will_fail)
            .then(add_ten)
            .catch(handle_error)
        )

        initial_promise.resolve(5)

        assert final_promise.is_fulfilled
        assert final_promise.value == "Handled: Failed on 10"

    def test_resolve_value_static(self):
        """Test the static resolve_value method."""
        promise = Promise.resolve_value("test")

        assert promise.is_fulfilled
        assert promise.value == "test"

    def test_reject_with_static(self):
        """Test the static reject_with method."""
        error = ValueError("test error")
        promise = Promise.reject_with(error)

        assert promise.is_rejected
        assert promise.reason is error

    def test_all(self):
        """Test the Promise.all static method."""
        promises: List[Promise[Any]] = [
            Promise[int](),
            Promise[str](),
            Promise[float]()
        ]

        all_promise = Promise.all(promises)

        # Initially pending
        assert all_promise.is_pending

        # Resolve the promises
        promises[0].resolve(1)
        promises[1].resolve("test")
        promises[2].resolve(3.14)

        # Now fulfilled with all values
        assert all_promise.is_fulfilled
        assert all_promise.value == [1, "test", 3.14]

    def test_all_with_rejection(self):
        """Test Promise.all with a rejection."""
        promises: List[Promise[Any]] = [
            Promise[int](),
            Promise[str](),
            Promise[float]()
        ]

        all_promise = Promise.all(promises)
        error = ValueError("test error")

        # Reject one promise
        promises[1].reject(error)

        # The all_promise should be rejected with the same error
        assert all_promise.is_rejected
        assert all_promise.reason is error

        # Resolving the other promises shouldn't change anything
        promises[0].resolve(1)
        promises[2].resolve(3.14)

        assert all_promise.is_rejected
        assert all_promise.reason is error

    def test_race(self):
        """Test the Promise.race static method."""
        promises: List[Promise[Any]] = [
            Promise[int](),
            Promise[str](),
            Promise[float]()
        ]

        race_promise = Promise.race(promises)

        # Initially pending
        assert race_promise.is_pending

        # Resolve the second promise first
        promises[1].resolve("winner")

        # The race_promise should be fulfilled with that value
        assert race_promise.is_fulfilled
        assert race_promise.value == "winner"

        # Resolving or rejecting other promises shouldn't change anything
        promises[0].resolve(1)
        promises[2].reject(ValueError("too late"))

        assert race_promise.is_fulfilled
        assert race_promise.value == "winner"

    def test_metadata(self):
        """Test the metadata capabilities for DevSynth analysis."""
        promise = Promise()

        # Set metadata
        promise.set_metadata("source", "test_module")
        promise.set_metadata("capability", "data_processing")
        promise.set_metadata("tags", ["important", "critical"])

        # Get metadata
        assert promise.get_metadata("source") == "test_module"
        assert promise.get_metadata("capability") == "data_processing"
        assert promise.get_metadata("tags") == ["important", "critical"]
        assert promise.get_metadata("nonexistent") is None
