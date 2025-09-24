"""Benchmarks for API endpoints. ReqID: PERF-03"""

import pytest

pytest.importorskip("pytest_benchmark")
pytest.importorskip("pytest_benchmark.plugin")


@pytest.mark.slow
def test_health_endpoint_benchmark(benchmark):
    """Benchmark the /health endpoint. ReqID: PERF-03"""
    pytest.importorskip("fastapi")
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient

    from devsynth.api import app

    client = TestClient(app)
    benchmark(lambda: client.get("/health"))
