import pytest


@pytest.mark.no_network
@pytest.mark.fast
def test_api_health_and_metrics_startup_without_binding_ports():
    """Metrics endpoint returns consistent counters without binding ports. ReqID: N/A"""
    pytest.importorskip("fastapi")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    # Import the app from the lightweight API module that includes /health and /metrics
    api_mod = __import__("devsynth.api", fromlist=["app"])  # type: ignore[assignment]
    app = getattr(api_mod, "app")

    client = TestClient(app)

    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json().get("status") == "ok"

    # Metrics should be available and consistent
    client.get("/metrics")  # prime counter for /metrics
    r_metrics = client.get("/metrics")
    assert r_metrics.status_code == 200
    metrics_text = r_metrics.text
    assert isinstance(metrics_text, str)

    assert 'request_count_total{endpoint="/health"} 1.0' in metrics_text
    assert 'request_count_total{endpoint="/metrics"} 1.0' in metrics_text


@pytest.mark.no_network
@pytest.mark.fast
def test_agent_openapi_documents_workflow_models():
    """OpenAPI schema surfaces shared workflow models and live endpoints."""

    pytest.importorskip("fastapi")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    api_mod = __import__("devsynth.api", fromlist=["app"])  # type: ignore[assignment]
    app = getattr(api_mod, "app")

    client = TestClient(app)

    schema = client.get("/openapi.json").json()
    components = schema.get("components", {}).get("schemas", {})
    assert "WorkflowResponse" in components
    workflow_properties = components["WorkflowResponse"]["properties"]
    assert workflow_properties["messages"]["items"]["type"] == "string"
    assert "metadata" in workflow_properties

    from devsynth.interface import agentapi as agentapi_module

    agentapi_module.LATEST_MESSAGES = ("integration ready",)

    status = client.get("/api/status")
    assert status.status_code == 200
    assert status.json() == {"messages": ["integration ready"], "metadata": None}
