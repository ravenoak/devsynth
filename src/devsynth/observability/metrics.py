"""Lightweight metrics helpers for DevSynth.

This module provides optional Prometheus metrics that activate only when
`prometheus_client` is importable (installed via the `api` extra). When not
available, all functions degrade to safe no-ops so importing this module never
introduces hard dependencies.

Usage:
    from devsynth.observability.metrics import increment_counter
    increment_counter("devsynth_cli_run_tests_invocations", {"target": target})

The helpers favor simplicity and stability for CLI/server contexts while keeping
allocation overhead minimal.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

try:  # pragma: no cover - import guard
    from prometheus_client import Counter  # type: ignore
except Exception:  # pragma: no cover - absent or broken client
    Counter = None  # type: ignore[assignment]

# Registry of created counters to avoid re-definitions with conflicting types
_COUNTERS: Dict[Tuple[str, Tuple[str, ...]], object] = {}


def _labels_tuple(labels: Optional[Dict[str, str]]) -> Tuple[str, ...]:
    if not labels:
        return tuple()
    # Sort keys to make label set stable
    return tuple(sorted(labels.keys()))


def increment_counter(name: str, labels: Optional[Dict[str, str]] = None, *, description: str = "") -> None:
    """Increment a Prometheus counter if available, otherwise no-op.

    Args:
        name: Metric name in snake_case following Prometheus conventions.
        labels: Optional labels mapping; values are coerced to str by Prometheus client.
        description: Optional human-friendly help text.
    """
    if Counter is None:  # No prometheus installed; no-op
        return

    label_names = _labels_tuple(labels)
    key = (name, label_names)
    metric = _COUNTERS.get(key)

    if metric is None:
        # Create counter lazily; if description is empty, provide a minimal default
        help_text = description or name.replace("_", " ")
        metric = Counter(name, help_text, list(label_names))  # type: ignore[call-arg]
        _COUNTERS[key] = metric

    if label_names:
        # Order values to match the sorted label names
        label_values = [str(labels[k]) for k in label_names]  # type: ignore[index]
        metric.labels(*label_values).inc()  # type: ignore[call-arg, union-attr]
    else:
        metric.inc()  # type: ignore[union-attr]
