"""Sentinel tests to ensure marker categories are always present.

These tests are intentionally trivial, deterministic, and extremely fast.
They serve as guardrails for scripts/verify_test_markers.py and CI shape,
so that the suite consistently contains at least one test per speed bucket.

Style and design notes:
- No network, no filesystem writes, no sleeps.
- If pytest is unavailable in a minimal environment, we install a no-op
  fallback for pytest.mark to avoid import-time errors while preserving
  decorator syntax for marker discovery.
- Aligns with .junie/guidelines.md (determinism, clarity, graceful failure) and
  docs/plan.md (stabilize CI/test categorization).
"""

from __future__ import annotations

# Provide a safe fallback if pytest is not installed, to avoid import-time
# collection errors in environments that only run verification scripts.
try:  # pragma: no cover - trivial import guard
    import pytest  # type: ignore
except Exception:  # pragma: no cover - exercised only in minimal envs

    class _NoOpDecoratorFactory:
        def __getattr__(self, _name):
            def _decorator(func):
                return func

            return _decorator

    class _NoOpPytest:
        mark = _NoOpDecoratorFactory()

    pytest = _NoOpPytest()  # type: ignore


@pytest.mark.no_network
@pytest.mark.fast
def test_sentinel_fast_bucket_present():
    """Fast bucket sentinel: executes in << 1s and is deterministic.

    ReqID: TR-01
    """
    # Arrange
    a, b = 1, 2
    # Act
    result = a + b
    # Assert
    assert result == 3


@pytest.mark.no_network
@pytest.mark.medium
def test_sentinel_medium_bucket_present():
    """Medium bucket sentinel: trivial logic, simply marks presence.

    ReqID: TR-01
    """
    data = [1, 1, 2, 3, 5]
    assert sum(data[:3]) == 4


@pytest.mark.no_network
@pytest.mark.slow
def test_sentinel_slow_bucket_present():
    """Slow bucket sentinel: instant execution, only ensures marker coverage.

    Note: We intentionally avoid sleeps; the 'slow' designation is semantic for
    categorization and does not enforce wall-clock runtime here.

    ReqID: TR-01
    """
    product = 1
    for x in (1, 1, 1):
        product *= x
    assert product == 1
