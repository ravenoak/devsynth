"""Utility module for tracking runtime metrics."""

from collections import Counter
from typing import Dict

# Counters for operations
_memory_metrics: Counter = Counter()
_provider_metrics: Counter = Counter()
_retry_metrics: Counter = Counter()
# Per-function retry count metrics
_retry_count_metrics: Counter = Counter()
# Per-exception retry metrics
_retry_error_metrics: Counter = Counter()


def inc_memory(op: str) -> None:
    """Increment memory operation counter."""
    _memory_metrics[op] += 1


def inc_provider(op: str) -> None:
    """Increment provider operation counter."""
    _provider_metrics[op] += 1


def inc_retry(op: str) -> None:
    """Increment retry operation counter."""
    _retry_metrics[op] += 1


def inc_retry_count(func_name: str) -> None:
    """Increment retry count for a specific function."""
    _retry_count_metrics[func_name] += 1


def inc_retry_error(error_name: str) -> None:
    """Increment retry counter for a specific error type."""
    _retry_error_metrics[error_name] += 1


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
