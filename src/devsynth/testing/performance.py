from __future__ import annotations

import json
import time
from collections.abc import Iterable
from pathlib import Path


def _run_workload(workload: int) -> None:
    """Execute a simple CPU-bound workload for benchmarking.

    Args:
        workload: Number of iterations to perform.

    This helper intentionally discards its intermediate results; it merely
    performs arithmetic to consume CPU cycles.
    """
    total = 0
    for i in range(workload):
        total += i * i


def capture_baseline_metrics(
    workload: int, output_path: Path | None = None
) -> dict[str, float]:
    """Capture baseline metrics for a given workload.

    Args:
        workload: Number of operations to execute.
        output_path: Optional path to write metrics JSON.

    Returns:
        Metrics dictionary with workload, duration, and throughput.
    """
    start = time.perf_counter()
    _run_workload(workload)
    duration = time.perf_counter() - start
    throughput = workload / duration if duration else 0.0
    metrics: dict[str, float] = {
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
) -> list[dict[str, float]]:
    """Capture scalability metrics across multiple workloads.

    Args:
        workloads: Iterable of workload sizes.
        output_path: Optional path to write metrics JSON list.

    Returns:
        List of metrics dictionaries for each workload.
    """
    results: list[dict[str, float]] = []
    for workload in workloads:
        start = time.perf_counter()
        _run_workload(workload)
        duration = time.perf_counter() - start
        throughput = workload / duration if duration else 0.0
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


__all__ = ["capture_baseline_metrics", "capture_scalability_metrics"]
