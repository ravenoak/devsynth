import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from devsynth.api import app
from devsynth.interface.agentapi import (
    init_endpoint,
    gather_endpoint,
    synthesize_endpoint,
    spec_endpoint,
    test_endpoint,
    code_endpoint,
    doctor_endpoint,
    edrr_cycle_endpoint,
    status_endpoint,
    InitRequest,
    GatherRequest,
    SynthesizeRequest,
    SpecRequest,
    TestSpecRequest as APITestSpecRequest,
    CodeRequest,
    DoctorRequest,
    EDRRCycleRequest,
    LATEST_MESSAGES,
)


@pytest.fixture
def mock_settings():
    """Mock settings with a test token."""
    with patch('devsynth.api.settings') as mock_settings:
        mock_settings.access_token = 'test_token'
        yield mock_settings


@pytest.fixture
def client(mock_settings):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_cli_commands():
    """Mock the CLI command functions."""
    with patch('devsynth.application.cli.init_cmd') as mock_init, patch(
        'devsynth.application.cli.gather_cmd') as mock_gather, patch(
        'devsynth.application.cli.run_pipeline_cmd') as mock_run, patch(
        'devsynth.application.cli.spec_cmd') as mock_spec, patch(
        'devsynth.application.cli.test_cmd') as mock_test, patch(
        'devsynth.application.cli.code_cmd') as mock_code, patch(
        'devsynth.application.cli.commands.doctor_cmd.doctor_cmd'
        ) as mock_doctor, patch(
        'devsynth.application.cli.commands.edrr_cycle_cmd.edrr_cycle_cmd'
        ) as mock_edrr:

        def update_bridge(bridge, message='Success'):
            bridge.display_result(message)
        mock_init.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Init successful')
        mock_gather.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Gather successful')
        mock_run.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Synthesize successful')
        mock_spec.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Spec successful')
        mock_test.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Test successful')
        mock_code.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Code successful')
        mock_doctor.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Doctor successful')
        mock_edrr.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'EDRR cycle successful')
        yield {'init_cmd': mock_init, 'gather_cmd': mock_gather,
            'run_pipeline_cmd': mock_run, 'spec_cmd': mock_spec, 'test_cmd':
            mock_test, 'code_cmd': mock_code, 'doctor_cmd': mock_doctor,
            'edrr_cycle_cmd': mock_edrr}


def test_health_endpoint_requires_authentication_succeeds(client):
    """Test that the health endpoint requires authentication.

ReqID: N/A"""
    response = client.get('/health')
    assert response.status_code == 401
    response = client.get('/health', headers={'Authorization':
        'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.get('/health', headers={'Authorization':
        'Bearer test_token'})
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_metrics_endpoint_requires_authentication_succeeds(client):
    """Test that the metrics endpoint requires authentication.

ReqID: N/A"""
    response = client.get('/metrics')
    assert response.status_code == 401
    response = client.get('/metrics', headers={'Authorization':
        'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.get('/metrics', headers={'Authorization':
        'Bearer test_token'})
    assert response.status_code == 200


def test_init_endpoint_initializes_project_succeeds(mock_cli_commands):
    """Test that the init endpoint initializes a project.

ReqID: N/A"""
    request = InitRequest(path='.', project_root=None, language=None, goals
        =None)
    response = init_endpoint(request, token=None)
    assert response.messages == ['Init successful']
    mock_cli_commands['init_cmd'].assert_called_once_with(path='.',
        project_root=None, language=None, goals=None, bridge=
        mock_cli_commands['init_cmd'].call_args[1]['bridge'])


def test_gather_endpoint_collects_requirements_succeeds(mock_cli_commands):
    """Test that the gather endpoint collects requirements.

ReqID: N/A"""
    request = GatherRequest(goals='test goals', constraints=
        'test constraints', priority='high')
    response = gather_endpoint(request, token=None)
    assert response.messages == ['Gather successful']
    mock_cli_commands['gather_cmd'].assert_called_once_with(bridge=
        mock_cli_commands['gather_cmd'].call_args[1]['bridge'])


def test_synthesize_endpoint_runs_pipeline_succeeds(mock_cli_commands):
    """Test that the synthesize endpoint runs the pipeline.

ReqID: N/A"""
    request = SynthesizeRequest(target='unit')
    response = synthesize_endpoint(request, token=None)
    assert response.messages == ['Synthesize successful']
    mock_cli_commands['run_pipeline_cmd'].assert_called_once_with(target=
        'unit', bridge=mock_cli_commands['run_pipeline_cmd'].call_args[1][
        'bridge'])


def test_spec_endpoint_generates_specifications_succeeds(mock_cli_commands):
    """Test that the spec endpoint generates specifications from requirements.

ReqID: N/A"""
    request = SpecRequest(requirements_file='requirements.md')
    response = spec_endpoint(request, token=None)
    assert response.messages == ['Spec successful']
    mock_cli_commands['spec_cmd'].assert_called_once_with(requirements_file
        ='requirements.md', bridge=mock_cli_commands['spec_cmd'].call_args[
        1]['bridge'])


def test_test_endpoint_generates_tests_succeeds(mock_cli_commands):
    """Test that the test endpoint generates tests from specifications.

ReqID: N/A"""

    def update_bridge(bridge, **kwargs):
        bridge.display_result('Test successful')
        return True
    mock_cli_commands['test_cmd'].side_effect = update_bridge
    from devsynth.interface.agentapi import AgentAPI, APIBridge
    bridge = APIBridge()
    agent_api = AgentAPI(bridge)
    messages = agent_api.test(spec_file='specs.md', output_dir=None)
    assert messages == ['Test successful']
    mock_cli_commands['test_cmd'].assert_called_once()
    call_kwargs = mock_cli_commands['test_cmd'].call_args[1]
    assert call_kwargs['spec_file'] == 'specs.md'
    assert call_kwargs['output_dir'] is None
    assert 'bridge' in call_kwargs


def test_code_endpoint_generates_code_succeeds(mock_cli_commands):
    """Test that the code endpoint generates code from tests.

ReqID: N/A"""
    request = CodeRequest(output_dir=None)
    response = code_endpoint(request, token=None)
    assert response.messages == ['Code successful']
    mock_cli_commands['code_cmd'].assert_called_once_with(output_dir=None,
        bridge=mock_cli_commands['code_cmd'].call_args[1]['bridge'])


def test_doctor_endpoint_runs_diagnostics_succeeds(mock_cli_commands):
    """Test that the doctor endpoint runs diagnostics.

ReqID: N/A"""
    request = DoctorRequest(path='.', fix=False)
    response = doctor_endpoint(request, token=None)
    assert response.messages == ['Doctor successful']
    mock_cli_commands['doctor_cmd'].assert_called_once_with(path='.', fix=
        False, bridge=mock_cli_commands['doctor_cmd'].call_args[1]['bridge'])


def test_edrr_cycle_endpoint_runs_cycle_succeeds(mock_cli_commands):
    """Test that the edrr_cycle endpoint runs an EDRR cycle.

ReqID: N/A"""
    request = EDRRCycleRequest(prompt='test prompt', context=None,
        max_iterations=3)
    response = edrr_cycle_endpoint(request, token=None)
    assert response.messages == ['EDRR cycle successful']
    mock_cli_commands['edrr_cycle_cmd'].assert_called_once_with(prompt=
        'test prompt', context=None, max_iterations=3, bridge=
        mock_cli_commands['edrr_cycle_cmd'].call_args[1]['bridge'])


def test_status_endpoint_returns_messages_returns_expected_result():
    """Test that the status endpoint returns the latest messages.

ReqID: N/A"""
    LATEST_MESSAGES.clear()
    LATEST_MESSAGES.append('Status: running')
    response = status_endpoint(token=None)
    assert response.messages == ['Status: running']


@pytest.mark.skip(reason=
    'This test is redundant with test_test_endpoint_generates_tests and causes naming conflicts'
    )
def test_endpoint_succeeds(mock_cli_commands):
    """This test is skipped because it's redundant with test_test_endpoint_generates_tests.

ReqID: N/A"""
    pass


def test_endpoints_handle_errors_properly_raises_error(mock_cli_commands):
    """Test that the endpoints handle errors properly by returning appropriate HTTP exceptions.

ReqID: N/A"""
    mock_cli_commands['init_cmd'].side_effect = Exception('Test error')
    request = InitRequest(path='.', project_root=None, language=None, goals
        =None)
    with pytest.raises(HTTPException) as excinfo:
        init_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert 'Failed to initialize project' in excinfo.value.detail
