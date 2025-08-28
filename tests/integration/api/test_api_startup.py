import pytest


@pytest.mark.no_network
@pytest.mark.fast
def test_api_health_and_metrics_startup_without_binding_ports():
    fastapi = pytest.importorskip("fastapi")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    # Import the app from the lightweight API module that includes /health and /metrics
    api_mod = __import__("devsynth.api", fromlist=["app"])  # type: ignore[assignment]
    app = getattr(api_mod, "app")

    client = TestClient(app)

    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json().get("status") == "ok"

    # Metrics should be available and return 200 even when prometheus_client is absent
    r_metrics = client.get("/metrics")
    assert r_metrics.status_code == 200
    assert isinstance(r_metrics.text, str)
