"""Utility module for tracking runtime metrics.

The module exposes helper functions for incrementing counters used throughout
the project.  Internally the counters are maintained both as simple in-memory
``Counter`` objects for unit tests and as `prometheus_client` counters for
runtime scraping.
"""

from __future__ import annotations

from collections import Counter as DictCounter
from typing import Dict

# Attempt to import Prometheus metrics, falling back to no-op counters when the
# optional dependency is unavailable.  This allows the core system and tests to
# run in minimal environments where ``prometheus_client`` isn't installed.
try:  # pragma: no cover - import guarded for optional dependency
    from prometheus_client import Counter
except Exception:  # pragma: no cover - fallback for minimal environments

    class Counter:  # type: ignore[override]
        """Lightweight stand-in for :class:`prometheus_client.Counter`.

        The dummy implementation exposes the ``labels``, ``inc`` and ``clear``
        methods used throughout the codebase but performs no operations.  Using
        this class keeps metric calls lightweight when Prometheus support isn't
        installed without requiring additional conditionals at call sites.
        """

        def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
            pass

        def labels(self, *args: object, **kwargs: object) -> "Counter":
            return self

        def inc(self, *args: object, **kwargs: object) -> None:
            pass

        def clear(self) -> None:
            pass


# ---------------------------------------------------------------------------
# In-memory counters used by tests and internal introspection
# ---------------------------------------------------------------------------
_memory_metrics: DictCounter[str] = DictCounter()
_provider_metrics: DictCounter[str] = DictCounter()
_retry_metrics: DictCounter[str] = DictCounter()
# Per-function retry count metrics
_retry_count_metrics: DictCounter[str] = DictCounter()
# Per-exception retry metrics
_retry_error_metrics: DictCounter[str] = DictCounter()
# Per-condition retry abort metrics
_retry_condition_metrics: DictCounter[str] = DictCounter()
# Dashboard metrics
_dashboard_metrics: DictCounter[str] = DictCounter()
# Circuit breaker state metrics
_circuit_breaker_metrics: DictCounter[str] = DictCounter()

# ---------------------------------------------------------------------------
# Prometheus counters
# ---------------------------------------------------------------------------
_memory_counter = Counter(
    "devsynth_memory_operations_total", "Memory operations", ["op"]
)
_provider_counter = Counter(
    "devsynth_provider_operations_total", "Provider operations", ["op"]
)
retry_event_counter = Counter("devsynth_retry_events_total", "Retry events", ["status"])
retry_function_counter = Counter(
    "devsynth_retry_function_total", "Retry attempts per function", ["function"]
)
retry_error_counter = Counter(
    "devsynth_retry_errors_total", "Retry events grouped by exception", ["error_type"]
)
retry_condition_counter = Counter(
    "devsynth_retry_conditions_total",
    "Retry aborts grouped by failed condition",
    ["condition"],
)
# Dashboard events counter
dashboard_event_counter = Counter(
    "devsynth_dashboard_events_total", "Dashboard events", ["event"]
)
# Circuit breaker state transitions counter
circuit_breaker_state_counter = Counter(
    "devsynth_circuit_breaker_state_total",
    "Circuit breaker state transitions",
    ["function", "state"],
)


def inc_memory(op: str) -> None:
    """Increment memory operation counter."""
    _memory_metrics[op] += 1
    _memory_counter.labels(op=op).inc()


def inc_provider(op: str) -> None:
    """Increment provider operation counter."""
    _provider_metrics[op] += 1
    _provider_counter.labels(op=op).inc()


def inc_retry(op: str) -> None:
    """Increment retry operation counter."""
    _retry_metrics[op] += 1
    retry_event_counter.labels(status=op).inc()


def inc_retry_count(func_name: str) -> None:
    """Increment retry count for a specific function."""
    _retry_count_metrics[func_name] += 1
    retry_function_counter.labels(function=func_name).inc()


def inc_retry_error(error_name: str) -> None:
    """Increment retry counter for a specific error type."""
    _retry_error_metrics[error_name] += 1
    retry_error_counter.labels(error_type=error_name).inc()


def inc_retry_condition(condition_name: str) -> None:
    """Increment retry counter for a specific condition name."""
    _retry_condition_metrics[condition_name] += 1
    retry_condition_counter.labels(condition=condition_name).inc()


def inc_circuit_breaker_state(func_name: str, state: str) -> None:
    """Increment circuit breaker state transition metrics.

    Parameters
    ----------
    func_name : str
        Name of the protected function.
    state : str
        Circuit breaker state being recorded.
    """
    key = f"{func_name}:{state}"
    _circuit_breaker_metrics[key] += 1
    circuit_breaker_state_counter.labels(function=func_name, state=state).inc()


def inc_dashboard(event: str) -> None:
    """Increment dashboard event counter."""
    _dashboard_metrics[event] += 1
    dashboard_event_counter.labels(event=event).inc()


def get_memory_metrics() -> Dict[str, int]:
    """Return memory operation counters."""
    return dict(_memory_metrics)


def get_provider_metrics() -> Dict[str, int]:
    """Return provider operation counters."""
    return dict(_provider_metrics)


def get_retry_metrics() -> Dict[str, int]:
    """Return retry operation counters."""
    return dict(_retry_metrics)


def get_retry_count_metrics() -> Dict[str, int]:
    """Return retry counts per function."""
    return dict(_retry_count_metrics)


def get_retry_error_metrics() -> Dict[str, int]:
    """Return retry counts for each exception type."""
    return dict(_retry_error_metrics)


def get_retry_condition_metrics() -> Dict[str, int]:
    """Return retry counts grouped by failed condition name."""
    return dict(_retry_condition_metrics)


def get_circuit_breaker_state_metrics() -> Dict[str, int]:
    """Return circuit breaker state transition counts."""
    return dict(_circuit_breaker_metrics)


def get_dashboard_metrics() -> Dict[str, int]:
    """Return dashboard event counters."""
    return dict(_dashboard_metrics)


def reset_metrics() -> None:
    """Reset all metrics counters."""
    _memory_metrics.clear()
    _provider_metrics.clear()
    _retry_metrics.clear()
    _retry_count_metrics.clear()
    _retry_error_metrics.clear()
    _retry_condition_metrics.clear()
    _dashboard_metrics.clear()
    _circuit_breaker_metrics.clear()

    _memory_counter.clear()
    _provider_counter.clear()
    retry_event_counter.clear()
    retry_function_counter.clear()
    retry_error_counter.clear()
    retry_condition_counter.clear()
    dashboard_event_counter.clear()
    circuit_breaker_state_counter.clear()
