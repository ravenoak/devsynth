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

from typing import Dict, Optional, Tuple, cast

from devsynth.metrics import CounterFactory, CounterProtocol

try:  # pragma: no cover - import guard
    from prometheus_client import Counter as _PrometheusCounter
except Exception:  # pragma: no cover - absent or broken client
    _COUNTER_FACTORY: CounterFactory | None = None
else:
    _COUNTER_FACTORY = cast(CounterFactory, _PrometheusCounter)

# Registry of created counters to avoid re-definitions with conflicting types
_COUNTERS: dict[tuple[str, tuple[str, ...]], CounterProtocol] = {}


def _labels_tuple(labels: dict[str, str] | None) -> tuple[str, ...]:
    if not labels:
        return tuple()
    # Sort keys to make label set stable
    return tuple(sorted(labels.keys()))


def increment_counter(
    name: str, labels: dict[str, str] | None = None, *, description: str = ""
) -> None:
    """Increment a Prometheus counter if available, otherwise no-op.

    Args:
        name: Metric name in snake_case following Prometheus conventions.
        labels: Optional labels mapping; values are coerced to str by Prometheus client.
        description: Optional human-friendly help text.
    """
    counter_factory = _COUNTER_FACTORY
    if counter_factory is None:  # No prometheus installed; no-op
        return

    label_names = _labels_tuple(labels)
    key = (name, label_names)
    metric = _COUNTERS.get(key)

    if metric is None:
        # Create counter lazily; if description is empty, provide a minimal default
        help_text = description or name.replace("_", " ")
        metric = counter_factory(name, help_text, list(label_names))
        _COUNTERS[key] = metric

    if label_names:
        # Order values to match the sorted label names
        assert labels is not None
        label_values = [str(labels[k]) for k in label_names]
        metric.labels(*label_values).inc()
    else:
        metric.inc()
