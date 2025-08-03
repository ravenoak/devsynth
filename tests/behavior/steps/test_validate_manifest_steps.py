"""Steps for the validate manifest feature."""

import os
import pytest
from pathlib import Path
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import MagicMock

# Import CLI steps to satisfy feature background requirements
from .cli_commands_steps import *  # noqa: F401,F403 - re-export CLI steps

scenarios("../features/general/validate_manifest.feature")


@pytest.mark.medium
@given("a project with an invalid configuration file")
def project_with_invalid_config(tmp_project_dir, command_context):
    """Create an invalid configuration file for testing."""
    config_path = os.path.join(tmp_project_dir, ".devsynth", "project.yaml")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        f.write("invalid: [unclosed")  # Invalid YAML
    command_context["config_path"] = config_path
    return config_path


@pytest.mark.medium
@given("a project without a configuration file")
def project_without_config(tmp_project_dir, command_context):
    """Ensure no configuration file exists."""
    config_path = os.path.join(tmp_project_dir, ".devsynth", "project.yaml")
    if os.path.exists(config_path):
        os.remove(config_path)
    command_context["config_path"] = config_path
    return tmp_project_dir


@pytest.mark.medium
@given("a project with a missing schema file")
def project_with_missing_schema(tmp_project_dir, command_context):
    """Set up a project with a reference to a non-existent schema file."""
    schema_path = os.path.join(tmp_project_dir, "missing-schema.json")
    command_context["schema_path"] = schema_path
    return schema_path


@pytest.mark.medium
@then("the system should validate the project configuration")
def validate_project_config(mock_workflow_manager):
    """Verify that the system validated the project configuration."""
    mock_workflow_manager.execute_command.assert_any_call(
        "validate-manifest", {"config": None, "schema": None}
    )


@pytest.mark.medium
@then(parsers.parse('the system should validate the project configuration at "{path}"'))
def validate_project_config_at_path(path, mock_workflow_manager):
    """Verify that the system validated the project configuration at the specified path."""
    mock_workflow_manager.execute_command.assert_any_call(
        "validate-manifest", {"config": path, "schema": None}
    )


@pytest.mark.medium
@then(parsers.parse('the system should validate the project configuration against "{schema_path}"'))
def validate_project_config_against_schema(schema_path, mock_workflow_manager):
    """Verify that the system validated the project configuration against the specified schema."""
    mock_workflow_manager.execute_command.assert_any_call(
        "validate-manifest", {"config": None, "schema": schema_path}
    )


@pytest.mark.medium
@then("the output should indicate that the configuration is valid")
def check_config_valid_output(command_context):
    """Verify that the output indicates the configuration is valid."""
    output = command_context.get("output", "")
    assert "valid" in output.lower()


@pytest.mark.medium
@then("the system should display an error message")
def check_error_message_displayed(command_context):
    """Verify that an error message was displayed."""
    output = command_context.get("output", "")
    exit_code = command_context.get("exit_code", 0)
    assert exit_code != 0 or "error" in output.lower()


@pytest.mark.medium
@then("the error message should indicate the validation errors")
def check_validation_error_message(command_context):
    """Verify that the error message indicates validation errors."""
    output = command_context.get("output", "")
    assert "invalid" in output.lower() or "validation" in output.lower()


@pytest.mark.medium
@then("the error message should indicate that no configuration file was found")
def check_missing_config_error_message(command_context):
    """Verify that the error message indicates no configuration file was found."""
    output = command_context.get("output", "")
    assert "not found" in output.lower() or "missing" in output.lower()


@pytest.mark.medium
@then("the error message should indicate that the schema file was not found")
def check_missing_schema_error_message(command_context):
    """Verify that the error message indicates the schema file was not found."""
    output = command_context.get("output", "")
    assert "schema" in output.lower() and ("not found" in output.lower() or "missing" in output.lower())


@pytest.mark.medium
@then("the workflow should not execute successfully")
def check_workflow_failure(command_context):
    """Verify that the workflow did not execute successfully."""
    exit_code = command_context.get("exit_code", 0)
    assert exit_code != 0
