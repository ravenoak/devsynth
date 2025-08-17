"""Benchmarks for API endpoints. ReqID: PERF-03"""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from devsynth.api import app

client = TestClient(app)


@pytest.mark.slow
def test_health_endpoint_benchmark(benchmark):
    """Benchmark the /health endpoint. ReqID: PERF-03"""
    benchmark(lambda: client.get("/health"))
