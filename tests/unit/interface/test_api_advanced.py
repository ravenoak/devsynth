import pytest

pytest.importorskip("fastapi")

from unittest.mock import MagicMock, patch

from fastapi import HTTPException

# Defer fastapi.testclient import to avoid MRO issues during collection
# Import will be done lazily when actually needed by tests
TestClient = None

def _get_testclient():
    """Lazily import TestClient to avoid MRO issues during collection."""
    global TestClient
    if TestClient is None:
        try:
            from fastapi.testclient import TestClient
        except TypeError:
            # Fallback for MRO compatibility issues
            from starlette.testclient import TestClient
    return TestClient

from devsynth.api import app
from devsynth.application.cli._command_exports import COMMAND_ATTRIBUTE_NAMES
from devsynth.interface.agentapi import (
    LATEST_MESSAGES,
    CodeRequest,
    DoctorRequest,
    EDRRCycleRequest,
    GatherRequest,
    InitRequest,
    SpecRequest,
    SynthesizeRequest,
)
from devsynth.interface.agentapi import (
    TestSpecRequest as APITestSpecRequest,  # Uncommented closing parenthesis
)
from devsynth.interface.agentapi import (
    code_endpoint,
    doctor_endpoint,
    edrr_cycle_endpoint,
    gather_endpoint,
    init_endpoint,
    spec_endpoint,
    status_endpoint,
    synthesize_endpoint,
    test_endpoint,
)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("devsynth.api.settings") as mock_settings:
        mock_settings.API_TOKEN = "test_token"
        yield mock_settings


@pytest.fixture
def client(mock_settings):
    """Test client for the API."""
    return _get_testclient()(app)


@pytest.fixture
def mock_cli_commands():
    """Mock CLI commands for testing."""
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
        patch("devsynth.application.cli.init_cmd") as mock_init_cmd,
        patch("devsynth.application.cli.gather_cmd") as mock_gather_cmd,
        patch("devsynth.application.cli.run_pipeline_cmd") as mock_run_pipeline_cmd,
        patch("devsynth.application.cli.spec_cmd") as mock_spec_cmd,
        patch("devsynth.application.cli.test_cmd") as mock_test_cmd,
        patch("devsynth.application.cli.code_cmd") as mock_code_cmd,
        patch(
            "devsynth.application.cli.commands.doctor_cmd.doctor_cmd"
        ) as mock_doctor_cmd,
        patch(
            "devsynth.application.cli.commands.edrr_cycle_cmd.edrr_cycle_cmd"
        ) as mock_edrr_cycle_cmd,
    ):

        def update_bridge(bridge, message="Success"):
            bridge.display_result(message)
            return True

        def mock_init_handler(**kwargs):
            return update_bridge(kwargs["bridge"], "Init successful")

        def mock_gather_handler(**kwargs):
            return update_bridge(kwargs["bridge"], "Gather successful")

        def mock_run_pipeline_handler(**kwargs):
            return update_bridge(kwargs["bridge"], "Synthesize successful")

        def mock_spec_handler(**kwargs):
            return update_bridge(kwargs["bridge"], "Spec successful")

        def mock_test_handler(**kwargs):
            return update_bridge(kwargs["bridge"], "Test successful")

        def mock_code_handler(**kwargs):
            return update_bridge(kwargs["bridge"], "Code successful")

        def mock_doctor_handler(**kwargs):
            return update_bridge(kwargs["bridge"], "Doctor successful")

        def mock_edrr_cycle_handler(**kwargs):
            return update_bridge(kwargs["bridge"], "EDRR cycle successful")

        mock_init_cmd.side_effect = mock_init_handler
        mock_gather_cmd.side_effect = mock_gather_handler
        mock_run_pipeline_cmd.side_effect = mock_run_pipeline_handler
        mock_spec_cmd.side_effect = mock_spec_handler
        mock_test_cmd.side_effect = mock_test_handler
        mock_code_cmd.side_effect = mock_code_handler
        mock_doctor_cmd.side_effect = mock_doctor_handler
        mock_edrr_cycle_cmd.side_effect = mock_edrr_cycle_handler
        yield {
            "init_cmd": mock_init_cmd,
            "gather_cmd": mock_gather_cmd,
            "run_pipeline_cmd": mock_run_pipeline_cmd,
            "spec_cmd": mock_spec_cmd,
            "test_cmd": mock_test_cmd,
            "code_cmd": mock_code_cmd,
            "doctor_cmd": mock_doctor_cmd,
            "edrr_cycle_cmd": mock_edrr_cycle_cmd,
        }


@pytest.fixture
def clean_state():
    """Set up clean state for tests."""
    # Store original state of LATEST_MESSAGES
    original_messages = LATEST_MESSAGES.copy()

    # Clear any existing messages before test
    LATEST_MESSAGES.clear()

    yield

    # Clean up state after test
    LATEST_MESSAGES.clear()

    # Restore original messages
    LATEST_MESSAGES.extend(original_messages)


@pytest.mark.slow
def test_error_handling_in_all_endpoints(mock_cli_commands, clean_state):
    """Test error handling in all endpoints.

    ReqID: N/A"""
    mock_cli_commands["init_cmd"].side_effect = Exception("Init error")
    request = InitRequest(path=".", project_root=None, language=None, goals=None)
    with pytest.raises(HTTPException) as excinfo:
        init_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert "Failed to initialize project" in excinfo.value.detail
    mock_cli_commands["gather_cmd"].side_effect = Exception("Gather error")
    request = GatherRequest(
        goals="test goals", constraints="test constraints", priority="high"
    )
    with pytest.raises(HTTPException) as excinfo:
        gather_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert "Failed to gather requirements" in excinfo.value.detail
    mock_cli_commands["run_pipeline_cmd"].side_effect = Exception("Synthesize error")
    request = SynthesizeRequest(target="unit")
    with pytest.raises(HTTPException) as excinfo:
        synthesize_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert "Failed to run synthesis pipeline" in excinfo.value.detail
    mock_cli_commands["spec_cmd"].side_effect = Exception("Spec error")
    request = SpecRequest(requirements_file="requirements.md")
    with pytest.raises(HTTPException) as excinfo:
        spec_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert "Failed to generate spec" in excinfo.value.detail
    mock_cli_commands["test_cmd"].side_effect = Exception("Test error")
    request = APITestSpecRequest(spec_file="specs.md", output_dir=None)
    with pytest.raises(HTTPException) as excinfo:
        test_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert "Failed to generate tests" in excinfo.value.detail
    mock_cli_commands["code_cmd"].side_effect = Exception("Code error")
    request = CodeRequest(output_dir=None)
    with pytest.raises(HTTPException) as excinfo:
        code_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert "Failed to generate code" in excinfo.value.detail
    mock_cli_commands["doctor_cmd"].side_effect = Exception("Doctor error")
    request = DoctorRequest(path=".", fix=False)
    with pytest.raises(HTTPException) as excinfo:
        doctor_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert "Failed to run diagnostics" in excinfo.value.detail
    mock_cli_commands["edrr_cycle_cmd"].side_effect = Exception("EDRR error")
    request = EDRRCycleRequest(prompt="test prompt", context=None, max_iterations=3)
    with pytest.raises(HTTPException) as excinfo:
        edrr_cycle_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert "Failed to run EDRR cycle" in excinfo.value.detail


@pytest.mark.slow
def test_all_endpoints_authentication_succeeds(client, clean_state):
    """Test authentication for all endpoints.

    ReqID: N/A"""
    response = client.post("/api/init", json={"path": "."})
    assert response.status_code == 401
    response = client.post(
        "/api/init",
        json={"path": "."},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    response = client.post(
        "/api/gather",
        json={
            "goals": "test goals",
            "constraints": "test constraints",
            "priority": "high",
        },
    )
    assert response.status_code == 401
    response = client.post(
        "/api/gather",
        json={
            "goals": "test goals",
            "constraints": "test constraints",
            "priority": "high",
        },
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    response = client.post("/api/synthesize", json={"target": "unit"})
    assert response.status_code == 401
    response = client.post(
        "/api/synthesize",
        json={"target": "unit"},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    response = client.post("/api/spec", json={"requirements_file": "requirements.md"})
    assert response.status_code == 401
    response = client.post(
        "/api/spec",
        json={"requirements_file": "requirements.md"},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    response = client.post("/api/test", json={"spec_file": "specs.md"})
    assert response.status_code == 401
    response = client.post(
        "/api/test",
        json={"spec_file": "specs.md"},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    response = client.post("/api/code", json={})
    assert response.status_code == 401
    response = client.post(
        "/api/code", json={}, headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    response = client.post("/api/doctor", json={"path": ".", "fix": False})
    assert response.status_code == 401
    response = client.post(
        "/api/doctor",
        json={"path": ".", "fix": False},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    response = client.post("/api/edrr-cycle", json={"prompt": "test prompt"})
    assert response.status_code == 401
    response = client.post(
        "/api/edrr-cycle",
        json={"prompt": "test prompt"},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    response = client.get("/api/status")
    assert response.status_code == 401
    response = client.get(
        "/api/status", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


@pytest.mark.slow
def test_parameter_validation_is_valid(mock_cli_commands, clean_state):
    """Test validation of request parameters.

    ReqID: N/A"""
    request = InitRequest(path=None, project_root=None, language=None, goals=None)
    with pytest.raises(HTTPException) as excinfo:
        init_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "path is required" in excinfo.value.detail
    request = GatherRequest(goals=None, constraints=None, priority=None)
    with pytest.raises(HTTPException) as excinfo:
        gather_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "goals are required" in excinfo.value.detail
    request = SynthesizeRequest(target="invalid")
    with pytest.raises(HTTPException) as excinfo:
        synthesize_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "target must be one of" in excinfo.value.detail
    request = SpecRequest(requirements_file=None)
    with pytest.raises(HTTPException) as excinfo:
        spec_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "requirements_file is required" in excinfo.value.detail
    request = APITestSpecRequest(spec_file=None, output_dir=None)
    with pytest.raises(HTTPException) as excinfo:
        test_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "spec_file is required" in excinfo.value.detail
    request = EDRRCycleRequest(prompt=None, context=None, max_iterations=3)
    with pytest.raises(HTTPException) as excinfo:
        edrr_cycle_endpoint(request, token=None)
    assert excinfo.value.status_code == 400

    assert "prompt is required" in excinfo.value.detail


@pytest.mark.slow
def test_edge_cases_succeeds(mock_cli_commands, clean_state):
    """Test edge cases for API endpoints.

    ReqID: N/A"""
    request = InitRequest(path="", project_root=None, language=None, goals=None)
    with pytest.raises(HTTPException) as excinfo:
        init_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "path cannot be empty" in excinfo.value.detail
    request = GatherRequest(goals="", constraints=None, priority=None)
    with pytest.raises(HTTPException) as excinfo:
        gather_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "goals cannot be empty" in excinfo.value.detail
    request = SynthesizeRequest(target="")
    with pytest.raises(HTTPException) as excinfo:
        synthesize_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "target cannot be empty" in excinfo.value.detail
    request = SpecRequest(requirements_file="")
    with pytest.raises(HTTPException) as excinfo:
        spec_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "requirements_file cannot be empty" in excinfo.value.detail
    request = APITestSpecRequest(spec_file="", output_dir=None)
    with pytest.raises(HTTPException) as excinfo:
        test_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "spec_file cannot be empty" in excinfo.value.detail
    request = EDRRCycleRequest(prompt="", context=None, max_iterations=3)
    with pytest.raises(HTTPException) as excinfo:
        edrr_cycle_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "prompt cannot be empty" in excinfo.value.detail
    request = EDRRCycleRequest(prompt="test prompt", context=None, max_iterations=-1)
    with pytest.raises(HTTPException) as excinfo:
        edrr_cycle_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert "max_iterations must be positive" in excinfo.value.detail
