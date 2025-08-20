"""Benchmarks for API endpoints. ReqID: PERF-03"""

from importlib import util

import pytest

pytest.importorskip("pytest_benchmark")
if util.find_spec("pytest_benchmark.plugin") is None:
    pytest.skip("pytest-benchmark plugin not installed", allow_module_level=True)


@pytest.mark.slow
def test_health_endpoint_benchmark(benchmark):
    """Benchmark the /health endpoint. ReqID: PERF-03"""
    if util.find_spec("fastapi") is None:
        pytest.skip("fastapi required")

    from fastapi.testclient import TestClient

    from devsynth.api import app

    client = TestClient(app)
    benchmark(lambda: client.get("/health"))
