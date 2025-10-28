"""
Unit tests for the Promise system.
"""

from typing import Any, List, Optional

import pytest

from devsynth.application.promises import (
    Promise,
    PromiseError,
    PromiseState,
    PromiseStateError,
)


class TestPromise:
    """Test suite for the Promise class.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_initial_state_succeeds(self):
        """Test the initial state of a Promise.

        ReqID: N/A"""
        promise = Promise()
        assert promise.state == PromiseState.PENDING
        assert promise.is_pending
        assert not promise.is_fulfilled
        assert not promise.is_rejected

    @pytest.mark.fast
    def test_resolve_succeeds(self):
        """Test resolving a Promise.

        ReqID: N/A"""
        promise = Promise[str]()
        promise.resolve("test value")
        assert promise.state == PromiseState.FULFILLED
        assert promise.is_fulfilled
        assert not promise.is_pending
        assert promise.value == "test value"
        with pytest.raises(PromiseStateError):
            promise.resolve("another value")

    @pytest.mark.fast
    def test_reject_succeeds(self):
        """Test rejecting a Promise.

        ReqID: N/A"""
        promise = Promise()
        error = ValueError("test error")
        promise.reject(error)
        assert promise.state == PromiseState.REJECTED
        assert promise.is_rejected
        assert not promise.is_pending
        assert promise.reason is error
        with pytest.raises(PromiseStateError):
            promise.reject(Exception("another error"))

    @pytest.mark.fast
    def test_then_fulfilled_succeeds(self):
        """Test the 'then' method with a fulfilled Promise.

        ReqID: N/A"""
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

    @pytest.mark.fast
    def test_then_rejected_succeeds(self):
        """Test the 'then' method with a rejected Promise.

        ReqID: N/A"""
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

    @pytest.mark.fast
    def test_catch_succeeds(self):
        """Test the 'catch' method.

        ReqID: N/A"""
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

    @pytest.mark.fast
    def test_chaining_succeeds(self):
        """Test chaining multiple promises.

        ReqID: N/A"""
        initial_promise = Promise[int]()

        def double(x: int) -> int:
            return x * 2

        def add_ten(x: int) -> int:
            return x + 10

        def stringify(x: int) -> str:
            return f"Result: {x}"

        final_promise = initial_promise.then(double).then(add_ten).then(stringify)
        initial_promise.resolve(5)
        assert final_promise.is_fulfilled
        assert final_promise.value == "Result: 20"

    @pytest.mark.fast
    def test_error_propagation_raises_error(self):
        """Test error propagation through chains.

        ReqID: N/A"""
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
            initial_promise.then(double)
            .then(will_fail)
            .then(add_ten)
            .catch(handle_error)
        )
        initial_promise.resolve(5)
        assert final_promise.is_fulfilled
        assert final_promise.value == "Handled: Failed on 10"

    @pytest.mark.fast
    def test_resolve_value_static_succeeds(self):
        """Test the static resolve_value method.

        ReqID: N/A"""
        promise = Promise.resolve_value("test")
        assert promise.is_fulfilled
        assert promise.value == "test"

    @pytest.mark.fast
    def test_reject_with_static_succeeds(self):
        """Test the static reject_with method.

        ReqID: N/A"""
        error = ValueError("test error")
        promise = Promise.reject_with(error)
        assert promise.is_rejected
        assert promise.reason is error

    @pytest.mark.fast
    def test_all_succeeds(self):
        """Test the Promise.all static method.

        ReqID: N/A"""
        promises: list[Promise[Any]] = [
            Promise[int](),
            Promise[str](),
            Promise[float](),
        ]
        all_promise = Promise.all(promises)
        assert all_promise.is_pending
        promises[0].resolve(1)
        promises[1].resolve("test")
        promises[2].resolve(3.14)
        assert all_promise.is_fulfilled
        assert all_promise.value == [1, "test", 3.14]

    @pytest.mark.fast
    def test_all_with_rejection_succeeds(self):
        """Test Promise.all with a rejection.

        ReqID: N/A"""
        promises: list[Promise[Any]] = [
            Promise[int](),
            Promise[str](),
            Promise[float](),
        ]
        all_promise = Promise.all(promises)
        error = ValueError("test error")
        promises[1].reject(error)
        assert all_promise.is_rejected
        assert all_promise.reason is error
        promises[0].resolve(1)
        promises[2].resolve(3.14)
        assert all_promise.is_rejected
        assert all_promise.reason is error

    @pytest.mark.fast
    def test_race_succeeds(self):
        """Test the Promise.race static method.

        ReqID: N/A"""
        promises: list[Promise[Any]] = [
            Promise[int](),
            Promise[str](),
            Promise[float](),
        ]
        race_promise = Promise.race(promises)
        assert race_promise.is_pending
        promises[1].resolve("winner")
        assert race_promise.is_fulfilled
        assert race_promise.value == "winner"
        promises[0].resolve(1)
        promises[2].reject(ValueError("too late"))
        assert race_promise.is_fulfilled
        assert race_promise.value == "winner"

    @pytest.mark.fast
    def test_metadata_succeeds(self):
        """Test the metadata capabilities for DevSynth analysis.

        ReqID: N/A"""
        promise = Promise()
        promise.set_metadata("source", "test_module")
        promise.set_metadata("capability", "data_processing")
        promise.set_metadata("tags", ["important", "critical"])
        assert promise.get_metadata("source") == "test_module"
        assert promise.get_metadata("capability") == "data_processing"
        assert promise.get_metadata("tags") == ["important", "critical"]
        assert promise.get_metadata("nonexistent") is None
