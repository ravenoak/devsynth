"""Step definitions for doctor_command.feature."""

import pytest
from pytest_bdd import given, then, when

from .cli_commands_steps import run_command


@pytest.mark.medium
@when('I run the command "devsynth check"')
def run_check_alias(monkeypatch, mock_workflow_manager, command_context):
    """Invoke the doctor command via its check alias."""
    return run_command(
        "devsynth check", monkeypatch, mock_workflow_manager, command_context
    )


@pytest.mark.medium
@given("essential environment variables are missing")
def missing_env_vars(monkeypatch):
    """Remove environment variables required by the doctor command."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LM_STUDIO_ENDPOINT", raising=False)


@pytest.mark.medium
@then("the output should mention the missing variables")
def output_mentions_missing_vars(command_context):
    """Check that the command output references the missing variables."""
    output = command_context.get("output", "")
    assert "OPENAI_API_KEY" in output or "LM_STUDIO_ENDPOINT" in output


@pytest.mark.medium
@then("the output should mention that no project configuration was found")
def output_mentions_missing_project_config(command_context):
    """Assert the CLI reports missing project configuration."""
    output = command_context.get("output", "")
    assert "No project configuration found" in output


@pytest.mark.medium
@given("a config directory with invalid YAML")
def config_dir_with_invalid_yaml(tmp_path, monkeypatch):
    """Create a temporary config directory containing malformed YAML."""
    config_path = tmp_path / "config"
    config_path.mkdir()
    (config_path / "development.yml").write_text("invalid: [unclosed")
    monkeypatch.chdir(tmp_path)
    return config_path
