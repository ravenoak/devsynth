"""Benchmarks for API endpoints. ReqID: PERF-03"""

import pytest

pytest.importorskip("pytest_benchmark")
pytest.importorskip("pytest_benchmark.plugin")

if not getattr(pytest, "config", None) or not pytest.config.pluginmanager.hasplugin(
    "benchmark"
):
    pytest.skip("benchmark plugin disabled", allow_module_level=True)


@pytest.mark.slow
def test_health_endpoint_benchmark(benchmark):
    """Benchmark the /health endpoint. ReqID: PERF-03"""
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from devsynth.api import app

    client = TestClient(app)
    benchmark(lambda: client.get("/health"))
