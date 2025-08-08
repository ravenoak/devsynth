"""Utility module for tracking runtime metrics.

The module exposes helper functions for incrementing counters used throughout
the project.  Internally the counters are maintained both as simple in-memory
``Counter`` objects for unit tests and as `prometheus_client` counters for
runtime scraping.
"""

from __future__ import annotations

from collections import Counter as DictCounter
from typing import Dict

from prometheus_client import Counter

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

# ---------------------------------------------------------------------------
# Prometheus counters
# ---------------------------------------------------------------------------
_memory_counter = Counter(
    "devsynth_memory_operations_total", "Memory operations", ["op"]
)
_provider_counter = Counter(
    "devsynth_provider_operations_total", "Provider operations", ["op"]
)
retry_event_counter = Counter(
    "devsynth_retry_events_total", "Retry events", ["status"]
)
retry_function_counter = Counter(
    "devsynth_retry_function_total", "Retry attempts per function", ["function"]
)
retry_error_counter = Counter(
    "devsynth_retry_errors_total", "Retry events grouped by exception", ["error_type"]
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


def reset_metrics() -> None:
    """Reset all metrics counters."""
    _memory_metrics.clear()
    _provider_metrics.clear()
    _retry_metrics.clear()
    _retry_count_metrics.clear()
    _retry_error_metrics.clear()

    _memory_counter.clear()
    _provider_counter.clear()
    retry_event_counter.clear()
    retry_function_counter.clear()
    retry_error_counter.clear()

