import pytest
from unittest.mock import patch

from devsynth.core import workflows


def test_filter_args_removes_none_values():
    assert workflows.filter_args({"a": 1, "b": None, "c": 0}) == {"a": 1, "c": 0}


@pytest.mark.parametrize(
    "func,command,kwargs,expected",
    [
        (workflows.init_project, "init", {"path": "p"}, {"path": "p"}),
        (
            workflows.generate_specs,
            "spec",
            {"requirements_file": "req.md"},
            {"requirements_file": "req.md"},
        ),
        (
            workflows.generate_tests,
            "test",
            {"spec_file": "spec.md"},
            {"spec_file": "spec.md"},
        ),
        (
            workflows.generate_code,
            "code",
            {},
            {},
        ),
        (
            workflows.run_pipeline,
            "run-pipeline",
            {"target": "build"},
            {"target": "build"},
        ),
        (
            workflows.update_config,
            "config",
            {"key": "model", "value": "gpt-4"},
            {"key": "model", "value": "gpt-4"},
        ),
        (
            workflows.update_config,
            "config",
            {"key": "model", "value": None, "list_models": True},
            {"key": "model", "value": None, "list_models": True},
        ),
        (
            workflows.inspect_requirements,
            "inspect",
            {"input": "requirements.txt", "interactive": False},
            {"input": "requirements.txt", "interactive": False},
        ),
    ],
)
def test_wrappers_call_execute_command(func, command, kwargs, expected):
    with patch("devsynth.core.workflows.workflow_manager.execute_command") as mock:
        mock.return_value = {"success": True}
        result = func(**kwargs)
        mock.assert_called_once_with(command, expected)
        assert result == {"success": True}
