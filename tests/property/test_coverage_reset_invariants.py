"""Property tests for the coverage reset invariants.

DocRef: docs/analysis/coverage_reset_proof.md
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import List, Set
from collections.abc import Iterable

import pytest

try:  # pragma: no cover - Hypothesis is optional
    from hypothesis import given, settings
    from hypothesis import strategies as st
except Exception:  # pragma: no cover - skip when Hypothesis missing
    pytest.skip("hypothesis not available", allow_module_level=True)

import tests.conftest as conftest


class _FakeCoverageTracker:
    """Mimic coverage.Coverage for the reset invariant tests."""

    def __init__(self) -> None:
        self.lines: set[int] = set()

    def load(self, executed: Iterable[int]) -> None:
        self.lines = set(executed)

    def erase(self) -> None:
        self.lines.clear()


def _fake_coverage_namespace(tracker: _FakeCoverageTracker) -> SimpleNamespace:
    """Return an object that looks like the coverage module."""

    class _Coverage:  # pylint: disable=too-few-public-methods
        @staticmethod
        def current() -> _FakeCoverageTracker:
            return tracker

    return SimpleNamespace(Coverage=_Coverage)


def _invoke_reset() -> None:
    """Mirror the reset_coverage fixture logic without using pytest internals."""

    coverage_mod = getattr(conftest, "coverage", None)
    if not coverage_mod or not os.environ.get("PYTEST_XDIST_WORKER"):
        return
    cov = coverage_mod.Coverage.current()
    if cov:
        cov.erase()


@pytest.mark.property
@pytest.mark.medium
@given(
    test_runs=st.lists(
        st.sets(st.integers(min_value=0, max_value=10), max_size=8),
        min_size=1,
        max_size=12,
    )
)
@settings(max_examples=50)
def test_reset_clears_coverage_state(test_runs: list[set[int]]) -> None:
    """Lemma: reset() empties the tracker between tests.

    ReqID: COV-RESET-INV-01
    """

    tracker = _FakeCoverageTracker()
    monkey = pytest.MonkeyPatch()
    monkey.setenv("PYTEST_XDIST_WORKER", "gw0")
    monkey.setattr(
        conftest, "coverage", _fake_coverage_namespace(tracker), raising=False
    )
    try:
        for executed in test_runs:
            tracker.load(executed)
            _invoke_reset()
            assert (
                tracker.lines == set()
            ), "reset() must clear previously executed lines"
    finally:
        monkey.undo()


@pytest.mark.property
@pytest.mark.medium
@given(
    test_runs=st.lists(
        st.sets(st.integers(min_value=0, max_value=20), max_size=6),
        min_size=1,
        max_size=10,
    )
)
@settings(max_examples=50)
def test_reset_preserves_union_of_individual_runs(test_runs: list[set[int]]) -> None:
    """Theorem: total coverage equals the union of isolated test runs.

    ReqID: COV-RESET-INV-02
    """

    tracker = _FakeCoverageTracker()
    monkey = pytest.MonkeyPatch()
    monkey.setenv("PYTEST_XDIST_WORKER", "gw0")
    monkey.setattr(
        conftest, "coverage", _fake_coverage_namespace(tracker), raising=False
    )

    observed_union: set[int] = set()
    expected_union: set[int] = set()

    try:
        for executed in test_runs:
            assert (
                tracker.lines == set()
            ), "coverage state must be empty before each simulated run"
            tracker.load(executed)
            observed_union |= tracker.lines
            expected_union |= set(executed)
            _invoke_reset()
            assert tracker.lines == set(), "coverage state must be empty after reset"
    finally:
        monkey.undo()

    assert observed_union == expected_union
