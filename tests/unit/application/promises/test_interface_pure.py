"""Pure tests for the lightweight :mod:`promises.interface` helpers."""

from __future__ import annotations

import pytest

from devsynth.application.promises import BasicPromise, PromiseState
from devsynth.exceptions import PromiseStateError

pytestmark = pytest.mark.fast


def test_basic_promise_metadata_round_trip() -> None:
    """Metadata helpers behave as a simple dictionary wrapper.

    ReqID: N/A
    """

    promise = BasicPromise[int]()
    assert promise.get_metadata("unknown") is None
    chained = promise.set_metadata("stage", "draft")
    assert chained is promise
    assert promise.get_metadata("stage") == "draft"


def test_then_on_fulfilled_promise_invokes_callback_immediately() -> None:
    """``then`` executed post-resolution returns an already-fulfilled promise.

    ReqID: N/A
    """

    promise = BasicPromise[int]()
    promise.resolve(10)
    chained = promise.then(lambda value: value + 5)
    assert chained.is_fulfilled
    assert chained.value == 15
    assert promise.state is PromiseState.FULFILLED


def test_catch_on_rejected_promise_yields_handler_result() -> None:
    """``catch`` converts the rejection reason using the supplied callback.

    ReqID: N/A
    """

    promise = BasicPromise[int]()
    promise.reject(RuntimeError("boom"))
    handled = promise.catch(lambda exc: str(exc).upper())
    assert handled.is_fulfilled
    assert handled.value == "BOOM"
    with pytest.raises(PromiseStateError):
        _ = promise.value
    assert promise.reason.args == ("boom",)
