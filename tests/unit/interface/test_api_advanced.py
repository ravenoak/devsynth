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
    """Mock settings for testing."""
    with patch('devsynth.api.settings') as mock_settings:
        mock_settings.API_TOKEN = 'test_token'
        yield mock_settings


@pytest.fixture
def client(mock_settings):
    """Test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_cli_commands():
    """Mock CLI commands for testing."""
    with patch('devsynth.application.cli.init_cmd') as mock_init_cmd, patch(
        'devsynth.application.cli.gather_cmd') as mock_gather_cmd, patch(
        'devsynth.application.cli.run_pipeline_cmd'
        ) as mock_run_pipeline_cmd, patch('devsynth.application.cli.spec_cmd'
        ) as mock_spec_cmd, patch('devsynth.application.cli.test_cmd'
        ) as mock_test_cmd, patch('devsynth.application.cli.code_cmd'
        ) as mock_code_cmd, patch(
        'devsynth.application.cli.commands.doctor_cmd.doctor_cmd'
        ) as mock_doctor_cmd, patch(
        'devsynth.application.cli.commands.edrr_cycle_cmd.edrr_cycle_cmd'
        ) as mock_edrr_cycle_cmd:

        def update_bridge(bridge, message='Success'):
            bridge.display_result(message)
            return True
        mock_init_cmd.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Init successful')
        mock_gather_cmd.side_effect = lambda **kwargs: update_bridge(kwargs
            ['bridge'], 'Gather successful')
        mock_run_pipeline_cmd.side_effect = lambda **kwargs: update_bridge(
            kwargs['bridge'], 'Synthesize successful')
        mock_spec_cmd.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Spec successful')
        mock_test_cmd.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Test successful')
        mock_code_cmd.side_effect = lambda **kwargs: update_bridge(kwargs[
            'bridge'], 'Code successful')
        mock_doctor_cmd.side_effect = lambda **kwargs: update_bridge(kwargs
            ['bridge'], 'Doctor successful')
        mock_edrr_cycle_cmd.side_effect = lambda **kwargs: update_bridge(kwargs
            ['bridge'], 'EDRR cycle successful')
        yield {'init_cmd': mock_init_cmd, 'gather_cmd': mock_gather_cmd,
            'run_pipeline_cmd': mock_run_pipeline_cmd, 'spec_cmd':
            mock_spec_cmd, 'test_cmd': mock_test_cmd, 'code_cmd':
            mock_code_cmd, 'doctor_cmd': mock_doctor_cmd, 'edrr_cycle_cmd':
            mock_edrr_cycle_cmd}


def test_all_endpoints_error_handling_raises_error(mock_cli_commands):
    """Test error handling in all endpoints.

ReqID: N/A"""
    mock_cli_commands['init_cmd'].side_effect = Exception('Init error')
    request = InitRequest(path='.', project_root=None, language=None, goals
        =None)
    with pytest.raises(HTTPException) as excinfo:
        init_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert 'Failed to initialize project' in excinfo.value.detail
    mock_cli_commands['gather_cmd'].side_effect = Exception('Gather error')
    request = GatherRequest(goals='test goals', constraints=
        'test constraints', priority='high')
    with pytest.raises(HTTPException) as excinfo:
        gather_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert 'Failed to gather requirements' in excinfo.value.detail
    mock_cli_commands['run_pipeline_cmd'].side_effect = Exception(
        'Synthesize error')
    request = SynthesizeRequest(target='unit')
    with pytest.raises(HTTPException) as excinfo:
        synthesize_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert 'Failed to run synthesis pipeline' in excinfo.value.detail
    mock_cli_commands['spec_cmd'].side_effect = Exception('Spec error')
    request = SpecRequest(requirements_file='requirements.md')
    with pytest.raises(HTTPException) as excinfo:
        spec_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert 'Failed to generate spec' in excinfo.value.detail
    mock_cli_commands['test_cmd'].side_effect = Exception('Test error')
    request = APITestSpecRequest(spec_file='specs.md', output_dir=None)
    with pytest.raises(HTTPException) as excinfo:
        test_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert 'Failed to generate tests' in excinfo.value.detail
    mock_cli_commands['code_cmd'].side_effect = Exception('Code error')
    request = CodeRequest(output_dir=None)
    with pytest.raises(HTTPException) as excinfo:
        code_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert 'Failed to generate code' in excinfo.value.detail
    mock_cli_commands['doctor_cmd'].side_effect = Exception('Doctor error')
    request = DoctorRequest(path='.', fix=False)
    with pytest.raises(HTTPException) as excinfo:
        doctor_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert 'Failed to run diagnostics' in excinfo.value.detail
    mock_cli_commands['edrr_cycle_cmd'].side_effect = Exception('EDRR error')
    request = EDRRCycleRequest(prompt='test prompt', context=None,
        max_iterations=3)
    with pytest.raises(HTTPException) as excinfo:
        edrr_cycle_endpoint(request, token=None)
    assert excinfo.value.status_code == 500
    assert 'Failed to run EDRR cycle' in excinfo.value.detail


def test_all_endpoints_authentication_succeeds(client):
    """Test authentication for all endpoints.

ReqID: N/A"""
    response = client.post('/api/init', json={'path': '.'})
    assert response.status_code == 401
    response = client.post('/api/init', json={'path': '.'}, headers={
        'Authorization': 'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.post('/api/gather', json={'goals': 'test goals',
        'constraints': 'test constraints', 'priority': 'high'})
    assert response.status_code == 401
    response = client.post('/api/gather', json={'goals': 'test goals',
        'constraints': 'test constraints', 'priority': 'high'}, headers={
        'Authorization': 'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.post('/api/synthesize', json={'target': 'unit'})
    assert response.status_code == 401
    response = client.post('/api/synthesize', json={'target': 'unit'},
        headers={'Authorization': 'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.post('/api/spec', json={'requirements_file':
        'requirements.md'})
    assert response.status_code == 401
    response = client.post('/api/spec', json={'requirements_file':
        'requirements.md'}, headers={'Authorization': 'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.post('/api/test', json={'spec_file': 'specs.md'})
    assert response.status_code == 401
    response = client.post('/api/test', json={'spec_file': 'specs.md'},
        headers={'Authorization': 'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.post('/api/code', json={})
    assert response.status_code == 401
    response = client.post('/api/code', json={}, headers={'Authorization':
        'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.post('/api/doctor', json={'path': '.', 'fix': False})
    assert response.status_code == 401
    response = client.post('/api/doctor', json={'path': '.', 'fix': False},
        headers={'Authorization': 'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.post('/api/edrr-cycle', json={'prompt': 'test prompt'})
    assert response.status_code == 401
    response = client.post('/api/edrr-cycle', json={'prompt': 'test prompt'
        }, headers={'Authorization': 'Bearer invalid_token'})
    assert response.status_code == 401
    response = client.get('/api/status')
    assert response.status_code == 401
    response = client.get('/api/status', headers={'Authorization':
        'Bearer invalid_token'})
    assert response.status_code == 401


def test_parameter_validation_is_valid(mock_cli_commands):
    """Test validation of request parameters.

ReqID: N/A"""
    request = InitRequest(path=None, project_root=None, language=None,
        goals=None)
    with pytest.raises(HTTPException) as excinfo:
        init_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'path is required' in excinfo.value.detail
    request = GatherRequest(goals=None, constraints=None, priority=None)
    with pytest.raises(HTTPException) as excinfo:
        gather_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'goals are required' in excinfo.value.detail
    request = SynthesizeRequest(target='invalid')
    with pytest.raises(HTTPException) as excinfo:
        synthesize_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'target must be one of' in excinfo.value.detail
    request = SpecRequest(requirements_file=None)
    with pytest.raises(HTTPException) as excinfo:
        spec_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'requirements_file is required' in excinfo.value.detail
    request = APITestSpecRequest(spec_file=None, output_dir=None)
    with pytest.raises(HTTPException) as excinfo:
        test_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'spec_file is required' in excinfo.value.detail
    request = EDRRCycleRequest(prompt=None, context=None, max_iterations=3)
    with pytest.raises(HTTPException) as excinfo:
        edrr_cycle_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'prompt is required' in excinfo.value.detail


def test_edge_cases_succeeds(mock_cli_commands):
    """Test edge cases for API endpoints.

ReqID: N/A"""
    request = InitRequest(path='', project_root=None, language=None, goals=None
        )
    with pytest.raises(HTTPException) as excinfo:
        init_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'path cannot be empty' in excinfo.value.detail
    request = GatherRequest(goals='', constraints=None, priority=None)
    with pytest.raises(HTTPException) as excinfo:
        gather_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'goals cannot be empty' in excinfo.value.detail
    request = SynthesizeRequest(target='')
    with pytest.raises(HTTPException) as excinfo:
        synthesize_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'target cannot be empty' in excinfo.value.detail
    request = SpecRequest(requirements_file='')
    with pytest.raises(HTTPException) as excinfo:
        spec_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'requirements_file cannot be empty' in excinfo.value.detail
    request = APITestSpecRequest(spec_file='', output_dir=None)
    with pytest.raises(HTTPException) as excinfo:
        test_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'spec_file cannot be empty' in excinfo.value.detail
    request = EDRRCycleRequest(prompt='', context=None, max_iterations=3)
    with pytest.raises(HTTPException) as excinfo:
        edrr_cycle_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'prompt cannot be empty' in excinfo.value.detail
    request = EDRRCycleRequest(prompt='test prompt', context=None,
        max_iterations=-1)
    with pytest.raises(HTTPException) as excinfo:
        edrr_cycle_endpoint(request, token=None)
    assert excinfo.value.status_code == 400
    assert 'max_iterations must be positive' in excinfo.value.detail
