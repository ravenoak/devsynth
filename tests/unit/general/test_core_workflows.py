import json
import pytest
from unittest.mock import patch
from devsynth.core import workflows


def test_filter_args_removes_none_values_succeeds():
    """Test that filter args removes none values succeeds.

ReqID: N/A"""
    assert workflows.filter_args({'a': 1, 'b': None, 'c': 0}) == {'a': 1,
        'c': 0}


@pytest.mark.parametrize('func,command,kwargs,expected', [(workflows.
    init_project, 'init', {'path': 'p'}, {'path': 'p'}), (workflows.
    generate_specs, 'spec', {'requirements_file': 'req.md'}, {
    'requirements_file': 'req.md'}), (workflows.generate_tests, 'test', {
    'spec_file': 'spec.md'}, {'spec_file': 'spec.md'}), (workflows.
    generate_code, 'code', {}, {}), (workflows.run_pipeline, 'run-pipeline',
    {'target': 'build', 'report': None}, {'target': 'build'}), (workflows.
    update_config, 'config', {'key': 'model', 'value': 'gpt-4'}, {'key':
    'model', 'value': 'gpt-4'}), (workflows.update_config, 'config', {'key':
    'model', 'value': None, 'list_models': True}, {'key': 'model',
    'list_models': True}), (workflows.
    inspect_requirements, 'inspect', {'input': 'requirements.txt',
    'interactive': False}, {'input': 'requirements.txt', 'interactive': 
    False})])
def test_wrappers_call_execute_command_succeeds(func, command, kwargs, expected
    ):
    """Test that wrappers call execute command succeeds.

ReqID: N/A"""
    with patch('devsynth.core.workflows.execute_command') as mock:
        mock.return_value = {'success': True}
        result = func(**kwargs)
        mock.assert_called_once_with(command, expected)
        assert result == {'success': True}


def test_gather_requirements_creates_file_succeeds(tmp_path):
    """Test that gather requirements creates file succeeds.

ReqID: N/A"""


    class Bridge:

        def __init__(self):
            self.i = 0

        def prompt(self, *args, **kwargs):
            responses = ['goal1', 'constraint1', 'high']
            res = responses[self.i]
            self.i += 1
            return res

        def confirm(self, *a, **k):
            return True

        def display_result(self, *a, **k):
            pass
    output = tmp_path / 'req.json'
    workflows.gather_requirements(Bridge(), output_file=str(output))
    assert output.exists()
    data = json.load(open(output))
    assert data['priority'] == 'high'
