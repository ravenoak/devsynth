"""Benchmarks for API endpoints. ReqID: PERF-03"""

from importlib import util

import pytest


@pytest.mark.slow
def test_health_endpoint_benchmark(benchmark):
    """Benchmark the /health endpoint. ReqID: PERF-03"""
    if util.find_spec("fastapi") is None or util.find_spec("pytest_benchmark") is None:
        pytest.skip("fastapi and pytest-benchmark required")

    from fastapi.testclient import TestClient

    from devsynth.api import app

    client = TestClient(app)
    benchmark(lambda: client.get("/health"))
