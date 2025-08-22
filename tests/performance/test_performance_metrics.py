"""Stress tests for performance metrics. ReqID: PERF-05"""

import time

import pytest

from devsynth.application.performance import (
    capture_baseline_metrics,
    capture_scalability_metrics,
)


@pytest.mark.slow
def test_baseline_metrics(tmp_path):
    """Baseline metrics include throughput. ReqID: PERF-05"""
    path = tmp_path / "baseline.json"
    start = time.perf_counter()
    result = capture_baseline_metrics(100000, output_path=path)
    elapsed = time.perf_counter() - start
    assert result["throughput_ops_per_s"] > 0
    assert elapsed >= result["duration_seconds"]


@pytest.mark.slow
def test_scalability_metrics(tmp_path):
    """Scalability metrics cover multiple workloads. ReqID: PERF-05"""
    path = tmp_path / "scalability.json"
    workloads = [10000, 100000, 1000000]
    start = time.perf_counter()
    results = capture_scalability_metrics(workloads, output_path=path)
    elapsed = time.perf_counter() - start
    assert len(results) == len(workloads)
    assert elapsed >= max(r["duration_seconds"] for r in results)
