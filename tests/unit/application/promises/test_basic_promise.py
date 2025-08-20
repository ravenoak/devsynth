import pytest

from devsynth.application.promises import BasicPromise, PromiseState
from devsynth.exceptions import PromiseStateError


@pytest.mark.medium
def test_basic_promise_resolve_and_value():
    promise = BasicPromise[int]()
    promise.resolve(42)
    assert promise.is_fulfilled
    assert promise.value == 42
    assert promise.state is PromiseState.FULFILLED
    assert not promise.is_pending


def test_basic_promise_then_chains():
    first = BasicPromise[int]()
    chained = first.then(lambda x: x * 2)
    first.resolve(5)
    assert chained.is_fulfilled
    assert chained.value == 10


def test_basic_promise_catch_handles_rejection():
    first = BasicPromise[int]()
    chained = first.catch(lambda e: str(e))
    first.reject(RuntimeError("fail"))
    assert chained.is_fulfilled
    assert chained.value == "fail"


@pytest.mark.medium
def test_access_value_wrong_state_raises():
    promise = BasicPromise[int]()
    with pytest.raises(PromiseStateError):
        _ = promise.value
    with pytest.raises(PromiseStateError):
        _ = promise.reason
