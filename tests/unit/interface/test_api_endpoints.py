import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from devsynth.api import app
from devsynth.application.cli._command_exports import COMMAND_ATTRIBUTE_NAMES
from devsynth.interface import agentapi as agentapi_module
from devsynth.interface.agentapi import (
    code_endpoint,
    doctor_endpoint,
    edrr_cycle_endpoint,
    gather_endpoint,
    init_endpoint,
    spec_endpoint,
    status_endpoint,
    synthesize_endpoint,
)
from devsynth.interface.agentapi import test_endpoint as api_test_endpoint
from devsynth.interface.agentapi_models import (
    CodeRequest,
    DoctorRequest,
    EDRRCycleRequest,
    GatherRequest,
    HealthResponse,
    InitRequest,
    MetricsResponse,
    PriorityLevel,
    SpecRequest,
    SynthesisTarget,
    SynthesizeRequest,
    TestSpecRequest,
    WorkflowResponse,
)


@pytest.fixture
def enhanced_api():
    """Provide a reset enhanced agent API module for type-sensitive tests."""

    import devsynth.interface.agentapi_enhanced as agentapi_enhanced

    agentapi_enhanced.reset_state()
    return agentapi_enhanced


@pytest.fixture
def clean_state():
    """Set up clean state for tests."""
    original_messages = agentapi_module.LATEST_MESSAGES
    agentapi_module.LATEST_MESSAGES = tuple()

    yield

    agentapi_module.LATEST_MESSAGES = original_messages


@pytest.fixture
def mock_settings():
    """Mock settings with a test token."""
    with patch("devsynth.api.settings") as mock_settings:
        mock_settings.access_token = "test_token"
        yield mock_settings


@pytest.fixture
def client(mock_settings):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_cli_commands():
    """Mock the CLI command functions."""
    required = {
        "init_cmd",
        "gather_cmd",
        "run_pipeline_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "doctor_cmd",
        "edrr_cycle_cmd",
    }
    missing = required.difference(COMMAND_ATTRIBUTE_NAMES)
    if missing:  # pragma: no cover - defensive
        raise AssertionError(
            "CLI command exports missing expected attributes: "
            + ", ".join(sorted(missing))
        )
    with (
        patch("devsynth.application.cli.init_cmd") as mock_init,
        patch("devsynth.application.cli.gather_cmd") as mock_gather,
        patch("devsynth.application.cli.run_pipeline_cmd") as mock_run,
        patch("devsynth.application.cli.spec_cmd") as mock_spec,
        patch("devsynth.application.cli.test_cmd") as mock_test,
        patch("devsynth.application.cli.code_cmd") as mock_code,
        patch("devsynth.application.cli.commands.doctor_cmd.doctor_cmd") as mock_doctor,
        patch(
            "devsynth.application.cli.commands.edrr_cycle_cmd.edrr_cycle_cmd"
        ) as mock_edrr,
    ):

        def update_bridge(bridge, message="Success"):
            bridge.display_result(message)

        # Set up side effects for each mock
        mock_init.side_effect = lambda **kwargs: update_bridge(
            kwargs["bridge"], "Init successful"
        )
        mock_gather.side_effect = lambda **kwargs: update_bridge(
            kwargs["bridge"], "Gather successful"
        )
        mock_run.side_effect = lambda **kwargs: update_bridge(
            kwargs["bridge"], "Synthesize successful"
        )
        mock_spec.side_effect = lambda **kwargs: update_bridge(
            kwargs["bridge"], "Spec successful"
        )
        mock_test.side_effect = lambda **kwargs: update_bridge(
            kwargs["bridge"], "Test successful"
        )
        mock_code.side_effect = lambda **kwargs: update_bridge(
            kwargs["bridge"], "Code successful"
        )
        mock_doctor.side_effect = lambda **kwargs: update_bridge(
            kwargs["bridge"], "Doctor successful"
        )
        mock_edrr.side_effect = lambda **kwargs: update_bridge(
            kwargs["bridge"], "EDRR cycle successful"
        )

        yield {
            "init_cmd": mock_init,
            "gather_cmd": mock_gather,
            "run_pipeline_cmd": mock_run,
            "spec_cmd": mock_spec,
            "test_cmd": mock_test,
            "code_cmd": mock_code,
            "doctor_cmd": mock_doctor,
            "edrr_cycle_cmd": mock_edrr,
        }


@pytest.mark.medium
def test_health_endpoint_requires_authentication_succeeds(client, clean_state):
    """Test that the health endpoint requires authentication.

    ReqID: N/A"""
    response = client.get("/health")
    assert response.status_code == 401

    response = client.get("/health", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

    success = client.get("/health", headers={"Authorization": "Bearer test_token"})
    assert success.status_code == 200
    payload = HealthResponse.model_validate(success.json())
    assert payload.status == "ok"
    assert payload.uptime >= 0
    assert payload.additional_info is None


@pytest.mark.medium
def test_metrics_endpoint_requires_authentication_succeeds(client, clean_state):
    """Test that the metrics endpoint requires authentication.

    ReqID: N/A"""
    response = client.get("/metrics")
    assert response.status_code == 401

    response = client.get("/metrics", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

    success = client.get("/metrics", headers={"Authorization": "Bearer test_token"})
    assert success.status_code == 200
    metrics_lines = tuple(filter(None, success.text.splitlines()))
    metrics_payload = MetricsResponse(metrics=metrics_lines)
    assert any(
        line.startswith("api_uptime_seconds") for line in metrics_payload.metrics
    )
    assert any(
        line.startswith('endpoint_requests{endpoint="health"}')
        for line in metrics_payload.metrics
    )
    assert any(
        line.startswith('endpoint_requests{endpoint="metrics"}')
        for line in metrics_payload.metrics
    )


@pytest.mark.medium
def test_init_endpoint_initializes_project_succeeds(mock_cli_commands, clean_state):
    """Test that the init endpoint initializes a project.

    ReqID: N/A"""
    request = InitRequest(path=".")
    response = init_endpoint(request, token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("Init successful",)
    assert response.metadata is None
    assert agentapi_module.LATEST_MESSAGES == ("Init successful",)

    call_kwargs = mock_cli_commands["init_cmd"].call_args.kwargs
    assert call_kwargs["path"] == "."
    assert call_kwargs["project_root"] is None
    assert call_kwargs["language"] is None
    assert call_kwargs["goals"] is None
    assert "bridge" in call_kwargs


@pytest.mark.medium
def test_gather_endpoint_collects_requirements_succeeds(mock_cli_commands, clean_state):
    """Test that the gather endpoint collects requirements.

    ReqID: N/A"""
    request = GatherRequest(
        goals="test goals", constraints="test constraints", priority=PriorityLevel.HIGH
    )
    response = gather_endpoint(request, token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("Gather successful",)
    assert agentapi_module.LATEST_MESSAGES == ("Gather successful",)

    mock_cli_commands["gather_cmd"].assert_called_once()
    assert "bridge" in mock_cli_commands["gather_cmd"].call_args.kwargs


@pytest.mark.medium
def test_synthesize_endpoint_runs_pipeline_succeeds(mock_cli_commands, clean_state):
    """Test that the synthesize endpoint runs the pipeline.

    ReqID: N/A"""
    request = SynthesizeRequest(target=SynthesisTarget.UNIT)
    response = synthesize_endpoint(request, token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("Synthesize successful",)
    assert agentapi_module.LATEST_MESSAGES == ("Synthesize successful",)

    call_kwargs = mock_cli_commands["run_pipeline_cmd"].call_args.kwargs
    assert call_kwargs["target"] == SynthesisTarget.UNIT
    assert "bridge" in call_kwargs


@pytest.mark.medium
def test_spec_endpoint_generates_specifications_succeeds(
    mock_cli_commands, clean_state
):
    """Test that the spec endpoint generates specifications from requirements.

    ReqID: N/A"""
    request = SpecRequest(requirements_file="requirements.md")
    response = spec_endpoint(request, token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("Spec successful",)
    assert agentapi_module.LATEST_MESSAGES == ("Spec successful",)

    call_kwargs = mock_cli_commands["spec_cmd"].call_args.kwargs
    assert call_kwargs["requirements_file"] == "requirements.md"
    assert "bridge" in call_kwargs


@pytest.mark.medium
def test_test_endpoint_generates_tests_succeeds(mock_cli_commands, clean_state):
    """Test that the test endpoint generates tests from specifications.

    ReqID: N/A"""
    request = TestSpecRequest(spec_file="specs.md")
    response = api_test_endpoint(request, token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("Test successful",)
    assert agentapi_module.LATEST_MESSAGES == ("Test successful",)

    call_kwargs = mock_cli_commands["test_cmd"].call_args.kwargs
    assert call_kwargs["spec_file"] == "specs.md"
    assert call_kwargs["output_dir"] is None
    assert "bridge" in call_kwargs


@pytest.mark.medium
def test_code_endpoint_generates_code_succeeds(mock_cli_commands, clean_state):
    """Test that the code endpoint generates code from tests.

    ReqID: N/A"""
    request = CodeRequest(output_dir=None)
    response = code_endpoint(request, token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("Code successful",)
    assert agentapi_module.LATEST_MESSAGES == ("Code successful",)

    call_kwargs = mock_cli_commands["code_cmd"].call_args.kwargs
    assert call_kwargs["output_dir"] is None
    assert "bridge" in call_kwargs


@pytest.mark.medium
def test_doctor_endpoint_runs_diagnostics_succeeds(mock_cli_commands, clean_state):
    """Test that the doctor endpoint runs diagnostics.

    ReqID: N/A"""
    request = DoctorRequest(path=".", fix=False)
    response = doctor_endpoint(request, token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("Doctor successful",)
    assert agentapi_module.LATEST_MESSAGES == ("Doctor successful",)

    call_kwargs = mock_cli_commands["doctor_cmd"].call_args.kwargs
    assert call_kwargs["path"] == "."
    assert call_kwargs["fix"] is False
    assert "bridge" in call_kwargs


@pytest.mark.medium
def test_edrr_cycle_endpoint_runs_cycle_succeeds(mock_cli_commands, clean_state):
    """Test that the edrr_cycle endpoint runs an EDRR cycle.

    ReqID: N/A"""
    request = EDRRCycleRequest(prompt="test prompt", context=None, max_iterations=3)
    response = edrr_cycle_endpoint(request, token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("EDRR cycle successful",)
    assert agentapi_module.LATEST_MESSAGES == ("EDRR cycle successful",)

    call_kwargs = mock_cli_commands["edrr_cycle_cmd"].call_args.kwargs
    assert call_kwargs["prompt"] == "test prompt"
    assert call_kwargs["context"] is None
    assert call_kwargs["max_iterations"] == 3
    assert "bridge" in call_kwargs


@pytest.mark.medium
def test_status_endpoint_returns_messages_returns_expected_result(clean_state):
    """Test that the status endpoint returns the latest messages.

    ReqID: N/A"""
    agentapi_module.LATEST_MESSAGES = ("Status: running",)
    response = status_endpoint(token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("Status: running",)


@pytest.mark.medium
def test_test_endpoint_generates_tests_from_spec_succeeds(
    mock_cli_commands, clean_state
):
    """Test that the test endpoint generates tests from a specification file.

    ReqID: FR-17"""
    request = TestSpecRequest(spec_file="specs.md", output_dir="out")
    response = api_test_endpoint(request, token=None)
    assert isinstance(response, WorkflowResponse)
    assert response.messages == ("Test successful",)

    call_kwargs = mock_cli_commands["test_cmd"].call_args.kwargs
    assert call_kwargs["spec_file"] == "specs.md"
    assert call_kwargs["output_dir"] == "out"
    assert "bridge" in call_kwargs


@pytest.mark.medium
def test_endpoints_handle_errors_properly_raises_error(mock_cli_commands, clean_state):
    """Test that the endpoints handle errors properly by returning appropriate HTTP exceptions.

    ReqID: N/A"""
    mock_cli_commands["init_cmd"].side_effect = Exception("Test error")
    request = InitRequest(path=".", project_root=None, language=None, goals=None)
    with pytest.raises(HTTPException) as excinfo:
        init_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert "Failed to initialize project" in excinfo.value.detail


@pytest.mark.fast
def test_enhanced_rate_limit_state_tracks_buckets(enhanced_api):
    """Rate limiter maintains typed buckets across invocations.",

    ReqID: N/A"""

    request = SimpleNamespace(client=SimpleNamespace(host="1.2.3.4"))
    state = enhanced_api.AgentAPIState()

    enhanced_api.rate_limit(request, limit=2, window=30, state=state, current_time=1.0)
    enhanced_api.rate_limit(request, limit=2, window=30, state=state, current_time=2.0)

    assert state.rate_limiter.count("1.2.3.4") == 2
    bucket = state.rate_limiter.buckets["1.2.3.4"]
    assert all(isinstance(ts, float) for ts in bucket)

    with pytest.raises(enhanced_api.HTTPException) as exc:
        enhanced_api.rate_limit(
            request,
            limit=2,
            window=30,
            state=state,
            current_time=3.0,
        )

    detail = exc.value.detail
    assert detail["error"] == "Rate limit exceeded"
    assert tuple(detail.get("suggestions", ())) == ("Wait before retrying the request",)


@pytest.mark.fast
def test_enhanced_metrics_snapshot_typed(enhanced_api):
    """Metrics tracker exposes structured snapshots for serialization.",

    ReqID: N/A"""

    state = enhanced_api.AgentAPIState()
    state.metrics.increment("health")
    state.metrics.record_latency("health", 0.5)
    state.metrics.record_error()

    snapshot = state.metrics.snapshot()
    assert snapshot.request_count == 1
    assert snapshot.error_count == 1
    assert snapshot.endpoint_counts == {"health": 1}
    assert snapshot.endpoint_latency["health"] == (0.5,)


@pytest.mark.fast
def test_enhanced_init_endpoint_returns_typed_error(enhanced_api, tmp_path):
    """Initialization failures surface typed error payloads.",

    ReqID: N/A"""

    request = SimpleNamespace(client=SimpleNamespace(host="9.9.9.9"))
    init_request = InitRequest(path=str(tmp_path / "does-not-exist"))

    with pytest.raises(enhanced_api.HTTPException) as exc:
        enhanced_api.init_endpoint(request, init_request, token=None)

    detail = exc.value.detail
    assert detail["error"].startswith("Path not found")
    assert tuple(detail["suggestions"]) == (
        "Create the directory before initializing",
        "Check the path and try again",
    )
