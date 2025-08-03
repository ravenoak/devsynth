# Content from test_cli_commands_steps.py inlined here
"""
Step definitions for CLI Command Execution feature.
"""

import os
import sys
import logging
import pytest
from pytest_bdd import given, when, then, parsers
from unittest.mock import patch, MagicMock, ANY
from io import StringIO

# Import the CLI modules
from typer.testing import CliRunner
from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.cli_commands import (
    init_cmd,
    run_pipeline_cmd,
    config_cmd,
    edrr_cycle_cmd,
    inspect_cmd,
    refactor_cmd,
    serve_cmd,
    gather_cmd,
    webapp_cmd,
    dbschema_cmd,
)
from devsynth.application.cli.commands.validate_manifest_cmd import (
    validate_manifest_cmd,
)
from devsynth.application.cli.commands.validate_metadata_cmd import (
    validate_metadata_cmd,
)
from devsynth.application.cli.commands.alignment_metrics_cmd import (
    alignment_metrics_cmd,
)
from devsynth.application.cli.commands.inspect_code_cmd import inspect_code_cmd
from devsynth.application.cli.commands.inspect_config_cmd import inspect_config_cmd


@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    """
    Verify that the DevSynth CLI is installed.
    This is a precondition that's always true in the test environment.
    """
    # In a test environment, we assume the CLI is installed
    # We could check for the existence of the CLI module
    assert "devsynth" in sys.modules
    return True


@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_project_dir):
    """
    Set up a valid DevSynth project for testing.
    """
    # The tmp_project_dir fixture creates a temporary project directory
    return tmp_project_dir


@when(parsers.parse('I run the command "{command}"'))
def run_command(command, monkeypatch, mock_workflow_manager, command_context):
    """Execute a CLI command using Typer's CliRunner."""
    args = command.split()
    if args[0] == "devsynth":
        args = args[1:]

    command_context["command"] = command

    runner = CliRunner()

    if not os.environ.get("DEVSYNTH_NONINTERACTIVE"):
        monkeypatch.setattr(
            "devsynth.interface.cli.CLIUXBridge.ask_question",
            lambda self, _msg, **kw: kw.get("default", ""),
        )
        monkeypatch.setattr(
            "devsynth.interface.cli.CLIUXBridge.confirm_choice",
            lambda self, _msg, **kw: kw.get("default", True),
        )
    monkeypatch.setattr(
        "devsynth.application.cli.setup_wizard.SetupWizard.run",
        lambda self: None,
        raising=False,
    )

    with patch("uvicorn.run") as mock_run:
        result = runner.invoke(build_app(), args)
        if "serve" in args:
            command_context["uvicorn_call"] = mock_run.call_args

    command_context["output"] = result.output
    command_context["exit_code"] = result.exit_code


@then("the system should display the help information")
def check_help_displayed(command_context):
    """
    Verify that help information is displayed.
    """
    output = command_context.get("output", "")
    assert "DevSynth CLI" in output
    assert "Commands:" in output


@then("the output should include all available commands")
def check_commands_in_help(command_context):
    """
    Verify that all available commands are listed in the help output.
    """
    output = command_context.get("output", "")
    commands = [
        "init",
        "refactor",
        "inspect",
        "run-pipeline",
        "retrace",
        "config",
        "edrr-cycle",
        "validate-manifest",
        "help",
    ]
    for cmd in commands:
        assert cmd in output
    assert "adaptive" not in output
    assert "analyze" not in output


@then("the output should include usage examples")
def check_usage_examples(command_context):
    """
    Verify that usage examples are included in the help output.
    """
    output = command_context.get("output", "")
    assert "Run 'devsynth [COMMAND] --help'" in output


@then(parsers.parse('a new project should be created at "{path}"'))
def check_project_created(path, mock_workflow_manager):
    """
    Verify that a new project was created at the specified path.
    """
    # Check that the init command was called with the correct path
    mock_workflow_manager.execute_command.assert_any_call(
        "init",
        ANY,
    )


# This step definition matches exactly the text in the feature file
@then('the system should process the "custom-requirements.md" file')
def check_requirements_file_processed(mock_workflow_manager):
    """
    Verify that the system processed the custom requirements file.
    """
    mock_workflow_manager.execute_command.assert_any_call(
        "inspect", {"requirements_file": "custom-requirements.md"}
    )


# This step definition matches exactly the text in the feature file
@then('the system should process the "custom-specs.md" file')
def check_specs_file_processed(mock_workflow_manager):
    """
    Verify that the system processed the custom specs file.
    """
    mock_workflow_manager.execute_command.assert_any_call(
        "run-pipeline", {"target": "custom-specs.md"}
    )


@then(parsers.parse("generate specifications based on the requirements"))
def check_generate_specs(mock_workflow_manager):
    """
    Verify that specifications were generated based on requirements.
    """
    # This is covered by the check that the spec command was called
    assert mock_workflow_manager.execute_command.called


@then(parsers.parse("generate tests based on the specifications"))
def check_generate_tests(mock_workflow_manager):
    """
    Verify that tests were generated based on specifications.
    """
    # This is covered by the check that the test command was called
    assert mock_workflow_manager.execute_command.called


@then(
    parsers.parse("the system should generate {output_type} based on the {input_type}")
)
def check_generation(output_type, input_type, mock_workflow_manager, command_context):
    """
    Verify that the system generated the expected output based on the input.
    """
    # This is a more generic check that the workflow manager was called
    # The actual generation logic is tested in unit tests
    assert mock_workflow_manager.execute_command.called


@then(parsers.parse('the system should execute the "{target}" target'))
def check_target_executed(target, mock_workflow_manager):
    """
    Verify that the system executed the specified target.
    """
    mock_workflow_manager.execute_command.assert_any_call(
        "run-pipeline", {"target": target}
    )


@then(parsers.parse("the system should update the configuration"))
def check_config_updated(mock_workflow_manager):
    """
    Verify that the system updated the configuration.
    """
    assert mock_workflow_manager.execute_command.called
    # The specific key/value check is done in a separate step


@then(parsers.parse('set "{key}" to "{value}"'))
def check_config_key_value(key, value, mock_workflow_manager):
    """
    Verify that the system set the specified key to the specified value.
    """
    mock_workflow_manager.execute_command.assert_any_call(
        "config", {"key": key, "value": value}
    )


@then(parsers.parse('the system should display the value for "{key}"'))
def check_config_value_displayed(key, mock_workflow_manager):
    """
    Verify that the system displayed the value for the specified key.
    """
    mock_workflow_manager.execute_command.assert_any_call(
        "config", {"key": key, "value": None}
    )


@then("the system should display all configuration settings")
def check_all_config_displayed(mock_workflow_manager):
    """
    Verify that the system displayed all configuration settings.
    """
    mock_workflow_manager.execute_command.assert_any_call(
        "config", {"key": None, "value": None}
    )


@then("the workflow should execute successfully")
def check_workflow_success(mock_workflow_manager):
    """
    Verify that the workflow executed successfully.
    """
    # In our mocked setup, we assume success
    assert mock_workflow_manager.execute_command.called


@then("the system should display a success message")
def check_success_message(command_context):
    """
    Verify that a success message was displayed.
    """
    output = command_context.get("output", "")
    success_indicators = [
        "successfully",
        "success",
        "initialized",
        "generated",
        "executed",
        "updated",
        "complete",
        "enabled",
    ]

    # Check if any of the success indicators are in the output
    success_found = any(indicator in output.lower() for indicator in success_indicators)
    assert success_found, f"No success message found in output: {output}"


@then("indicate that the command is not recognized")
def check_command_not_recognized(command_context):
    """
    Verify that the system indicated that the command is not recognized.
    """
    # When an invalid command is provided, the help is shown
    output = command_context.get("output", "")
    assert "DevSynth CLI" in output
    assert "Commands:" in output


@given("a project with invalid environment configuration")
def project_with_invalid_env_config(tmp_project_dir):
    config_path = os.path.join(tmp_project_dir, "config")
    os.makedirs(config_path, exist_ok=True)
    with open(os.path.join(config_path, "development.yml"), "w") as f:
        f.write("application:\n  name: DevSynth\n")
    return tmp_project_dir


@given("valid environment configuration")
def valid_environment_config(tmp_project_dir):
    config_path = os.path.join(tmp_project_dir, "config")
    os.makedirs(config_path, exist_ok=True)
    for env in ["development", "testing"]:
        with open(os.path.join(config_path, f"{env}.yml"), "w") as f:
            f.write("application:\n  name: DevSynth\n")
    return tmp_project_dir


@then("the output should indicate configuration errors")
def check_config_errors(command_context):
    output = command_context.get("output", "")
    assert "warning" in output.lower() or "error" in output.lower()


@then(parsers.parse("the system should display a warning message"))
def check_warning_message(command_context):
    """Verify that the system displayed a warning message."""
    output = command_context.get("output", "")
    assert "warning" in output.lower() or "warning" in output


@then(parsers.parse('uvicorn should be called with host "{host}" and port {port:d}'))
def uvicorn_called_with(host, port, command_context):
    """Assert uvicorn.run was invoked with the specified host and port."""
    call = command_context.get("uvicorn_call")
    assert call is not None, "uvicorn.run was not called"
    args, kwargs = call
    if args:
        assert args[0] == "devsynth.api:app"
    assert kwargs.get("host") == host
    assert kwargs.get("port") == port


@given("essential environment variables are missing")
def missing_env_vars(monkeypatch):
    """Unset environment variables required for the doctor command."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LM_STUDIO_ENDPOINT", raising=False)


@given("a project with an invalid manifest file")
def invalid_manifest_file(tmp_project_dir):
    """Create a malformed manifest file in the project directory."""
    manifest_path = os.path.join(tmp_project_dir, "invalid_manifest.yaml")
    with open(manifest_path, "w") as f:
        f.write("invalid: [unclosed")
    return manifest_path


@then("the output should mention the missing variables")
def output_mentions_missing_vars(command_context):
    """Check that missing environment variables are referenced in output."""
    output = command_context.get("output", "")
    assert "OPENAI_API_KEY" in output or "LM_STUDIO_ENDPOINT" in output


# Step definitions for gather command
@then("the system should gather requirements interactively")
def check_gather_requirements_interactively(mock_workflow_manager):
    """Verify that the system gathered requirements interactively."""
    mock_workflow_manager.execute_command.assert_any_call(
        "gather", ANY
    )


@then(parsers.parse('save the requirements to "{output_file}"'))
def check_save_requirements_to_file(output_file, mock_workflow_manager):
    """Verify that the requirements were saved to the specified file."""
    mock_workflow_manager.execute_command.assert_any_call(
        "gather", {"output_file": output_file}
    )


# Step definitions for webapp command
@then(parsers.parse('the system should generate a Flask application at "{path}"'))
def check_generate_flask_application(path, mock_workflow_manager):
    """Verify that the system generated a Flask application at the specified path."""
    # Extract the name and path from the full path
    parts = path.split("/")
    name = parts[-1]
    path = "/".join(parts[:-1])
    
    mock_workflow_manager.execute_command.assert_any_call(
        "webapp", {"framework": "flask", "name": name, "path": path, "force": False}
    )


@then(parsers.parse('the system should generate a FastAPI application at "{path}"'))
def check_generate_fastapi_application(path, mock_workflow_manager):
    """Verify that the system generated a FastAPI application at the specified path."""
    # Extract the name and path from the full path
    parts = path.split("/")
    name = parts[-1]
    path = "/".join(parts[:-1])
    
    mock_workflow_manager.execute_command.assert_any_call(
        "webapp", {"framework": "fastapi", "name": name, "path": path, "force": False}
    )


@given(parsers.parse('a directory "{path}" already exists'))
def directory_already_exists(path, tmp_project_dir):
    """Create a directory that already exists."""
    full_path = os.path.join(tmp_project_dir, path)
    os.makedirs(full_path, exist_ok=True)
    return full_path


@then("suggest using the --force option")
def check_suggest_force_option(command_context):
    """Verify that the system suggested using the --force option."""
    output = command_context.get("output", "")
    assert "--force" in output


# Step definitions for dbschema command
@then(parsers.parse('the system should generate a SQLite database schema at "{path}"'))
def check_generate_sqlite_schema(path, mock_workflow_manager):
    """Verify that the system generated a SQLite database schema at the specified path."""
    # Extract the name and path from the full path
    parts = path.split("/")
    name = parts[-1].replace("_schema", "")
    path = "/".join(parts[:-1])
    
    mock_workflow_manager.execute_command.assert_any_call(
        "dbschema", {"db_type": "sqlite", "name": name, "path": path, "force": False}
    )


@then(parsers.parse('the system should generate a MySQL database schema at "{path}"'))
def check_generate_mysql_schema(path, mock_workflow_manager):
    """Verify that the system generated a MySQL database schema at the specified path."""
    # Extract the name and path from the full path
    parts = path.split("/")
    name = parts[-1].replace("_schema", "")
    path = "/".join(parts[:-1])
    
    mock_workflow_manager.execute_command.assert_any_call(
        "dbschema", {"db_type": "mysql", "name": name, "path": path, "force": False}
    )


@then(parsers.parse('the system should generate a MongoDB database schema at "{path}"'))
def check_generate_mongodb_schema(path, mock_workflow_manager):
    """Verify that the system generated a MongoDB database schema at the specified path."""
    # Extract the name and path from the full path
    parts = path.split("/")
    name = parts[-1].replace("_schema", "")
    path = "/".join(parts[:-1])
    
    mock_workflow_manager.execute_command.assert_any_call(
        "dbschema", {"db_type": "mongodb", "name": name, "path": path, "force": False}
    )

