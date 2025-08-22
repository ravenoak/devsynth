"""Performance measurement utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

OPS_PER_SECOND = 9_000_000


def _simulate_duration(workload: int, ops_per_second: float = OPS_PER_SECOND) -> float:
    """Return a deterministic duration for the workload."""
    return workload / ops_per_second


def capture_baseline_metrics(
    workload: int, output_path: Path | None = None
) -> Dict[str, float]:
    """Capture baseline metrics for a workload.

    Args:
        workload: Number of operations to simulate.
        output_path: Optional path to write the metrics JSON.

    Returns:
        Metrics dictionary with workload, duration, and throughput.
    """
    duration = _simulate_duration(workload)
    throughput = workload / duration if duration else 0.0
    metrics = {
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
) -> List[Dict[str, float]]:
    """Capture scalability metrics across workloads.

    Args:
        workloads: Iterable of workload sizes.
        output_path: Optional path to write the results JSON list.

    Returns:
        List of metrics dictionaries for each workload.
    """
    results = []
    for workload in workloads:
        duration = _simulate_duration(workload)
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
