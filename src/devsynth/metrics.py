"""Utility module for tracking runtime metrics."""

from collections import Counter
from typing import Dict

# Counters for operations
_memory_metrics: Counter = Counter()
_provider_metrics: Counter = Counter()
_retry_metrics: Counter = Counter()


def inc_memory(op: str) -> None:
    """Increment memory operation counter."""
    _memory_metrics[op] += 1


def inc_provider(op: str) -> None:
    """Increment provider operation counter."""
    _provider_metrics[op] += 1


def inc_retry(op: str) -> None:
    """Increment retry operation counter."""
    _retry_metrics[op] += 1


def get_memory_metrics() -> Dict[str, int]:
    """Return memory operation counters."""
    return dict(_memory_metrics)


def get_provider_metrics() -> Dict[str, int]:
    """Return provider operation counters."""
    return dict(_provider_metrics)


def get_retry_metrics() -> Dict[str, int]:
    """Return retry operation counters."""
    return dict(_retry_metrics)


def reset_metrics() -> None:
    """Reset all metrics counters."""
    _memory_metrics.clear()
    _provider_metrics.clear()
    _retry_metrics.clear()
