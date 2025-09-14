"""Performance measurement utilities.

Helpers to benchmark synthetic workloads. The functions here return
structured metrics to help evaluate the performance of basic CPU-bound
workloads. Metrics can optionally be written to JSON files for later
inspection.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable
from pathlib import Path
from typing import TypedDict


class PerformanceMetrics(TypedDict):
    """Measured metrics for a workload execution."""

    workload: int
    duration_seconds: float
    throughput_ops_per_s: float


def _run_workload(workload: int) -> int:
    """Execute a CPU-bound workload to benchmark.

    Args:
        workload: Number of loop iterations.

    Returns:
        Accumulated value from the synthetic workload.
    """
    total: int = 0
    for i in range(workload):
        total += i * i
    return total


def capture_baseline_metrics(
    workload: int, output_path: Path | None = None
) -> PerformanceMetrics:
    """Capture baseline metrics for a workload.

    Args:
        workload: Number of operations to execute.
        output_path: Optional path to write the metrics JSON.

    Returns:
        Metrics dictionary with workload, duration, and throughput.
    """
    start: float = time.perf_counter()
    _run_workload(workload)
    duration: float = time.perf_counter() - start
    throughput: float = workload / duration if duration else 0.0
    metrics: PerformanceMetrics = {
        "workload": workload,
        "duration_seconds": duration,
        "throughput_ops_per_s": throughput,
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(metrics, indent=2))
    return metrics


def capture_scalability_metrics(
    workloads: Iterable[int], output_path: Path | None = None
) -> list[PerformanceMetrics]:
    """Capture scalability metrics across workloads.

    Args:
        workloads: Iterable of workload sizes.
        output_path: Optional path to write the results JSON list.

    Returns:
        List of metrics dictionaries for each workload.
    """
    results: list[PerformanceMetrics] = []
    for workload in workloads:
        start: float = time.perf_counter()
        _run_workload(workload)
        duration: float = time.perf_counter() - start
        throughput: float = workload / duration if duration else 0.0
        results.append(
            {
                "workload": workload,
                "duration_seconds": duration,
                "throughput_ops_per_s": throughput,
            }
        )
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2))
    return results


__all__ = [
    "PerformanceMetrics",
    "capture_baseline_metrics",
    "capture_scalability_metrics",
]
