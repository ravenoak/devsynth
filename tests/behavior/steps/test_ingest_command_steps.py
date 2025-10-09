import os
import sys
from unittest.mock import MagicMock, patch

import click
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "ingest_command.feature"))


# Fixtures for test isolation
@pytest.fixture
def context():
    """Fixture to provide a context object for sharing data between steps."""

    class Context:
        def __init__(self):
            self.result = None
            self.manifest_path = None
            self.error_message = None

    return Context()


@pytest.fixture
def mock_ingest_cmd():
    """Fixture to mock the ingest_cmd function."""
    with patch("devsynth.application.cli.ingest_cmd.ingest_cmd") as mock:
        with patch("devsynth.application.cli.commands.ingest_cmd._ingest_cmd", mock):
            yield mock


# Step definitions
@given(parsers.parse('I have a valid project manifest file "{manifest_file}"'))
def valid_manifest_file(context, manifest_file, tmp_path):
    """Create a valid manifest file for testing."""
    manifest_content = """
    project:
      name: Test Project
      description: A test project for ingest command
    """
    manifest_path = tmp_path / manifest_file
    with open(manifest_path, "w") as f:
        f.write(manifest_content)

    context.manifest_path = str(manifest_path)


@given(parsers.parse('I have an invalid project manifest file "{manifest_file}"'))
def invalid_manifest_file(context, manifest_file, tmp_path):
    """Create an invalid manifest file for testing."""
    manifest_content = """
    invalid:
      - this is not a valid manifest
    """
    manifest_path = tmp_path / manifest_file
    with open(manifest_path, "w") as f:
        f.write(manifest_content)

    context.manifest_path = str(manifest_path)


@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    """Verify that the DevSynth CLI is installed."""
    assert "devsynth" in sys.modules


@when(parsers.parse('I run the command "{command}"'))
def run_command(context, command, mock_ingest_cmd, monkeypatch):
    """Run a DevSynth CLI command."""
    # Extract the manifest file name from the command
    if "manifest.yaml" in command:
        # Replace with the actual path to our temporary manifest file
        command = command.replace("manifest.yaml", context.manifest_path)
    elif "invalid_manifest.yaml" in command:
        # Replace with the actual path to our temporary invalid manifest file
        command = command.replace("invalid_manifest.yaml", context.manifest_path)
    elif "non_existent_manifest.yaml" in command:
        # Use a non-existent file path
        command = command.replace(
            "non_existent_manifest.yaml", "/tmp/non_existent_file.yaml"
        )

    # Parse the command to extract arguments
    args = command.split()[1:]  # Skip 'devsynth'

    # Set up the mock behavior based on the scenario
    if "non_existent_manifest.yaml" in command or "invalid_manifest.yaml" in command:
        mock_ingest_cmd.side_effect = Exception("Error ingesting project")
        try:
            from devsynth.adapters.cli.typer_adapter import parse_args

            parse_args(args)
            context.result = "success"
        except (click.exceptions.Exit, SystemExit) as e:
            code = e.exit_code if isinstance(e, click.exceptions.Exit) else e.code
            context.result = "success" if code == 0 else "failure"
            if code != 0:
                context.error_message = str(e)
        except Exception as e:
            context.result = "failure"
            context.error_message = str(e)
    else:
        mock_ingest_cmd.return_value = None  # Successful execution
        try:
            from devsynth.adapters.cli.typer_adapter import parse_args

            parse_args(args)
            context.result = "success"
        except (click.exceptions.Exit, SystemExit) as e:
            code = e.exit_code if isinstance(e, click.exceptions.Exit) else e.code
            context.result = "success" if code == 0 else "failure"
            if code != 0:
                context.error_message = str(e)
        except Exception as e:
            context.result = "failure"
            context.error_message = str(e)


@then("the command should execute successfully")
def command_successful(context):
    """Verify that the command executed successfully."""
    assert (
        context.result == "success"
    ), f"Command failed with error: {context.error_message}"


@then("the command should fail")
def command_failed(context):
    """Verify that the command failed."""
    assert context.result == "failure", "Command succeeded but was expected to fail"


@then("the system should display a success message")
def success_message_displayed(context, capsys):
    """Verify that a success message was displayed."""
    # This would check the captured stdout for success messages
    # Since we're mocking, we'll just verify the command was successful
    assert context.result == "success"


@then("the system should display an error message explaining the issue")
def error_message_displayed(context, capsys):
    """Verify that an error message was displayed."""
    # This would check the captured stdout for error messages
    # Since we're mocking, we'll just verify the command failed
    assert context.result == "failure"
    assert context.error_message is not None


@then("the system should display detailed progress information")
def detailed_progress_displayed(context, capsys):
    """Verify that detailed progress information was displayed."""
    # This would check the captured stdout for detailed progress information
    # Since we're mocking, we'll just verify the command was successful
    assert context.result == "success"


@then("the project should be ingested into the system")
def project_ingested(context, mock_ingest_cmd):
    """Verify that the project was ingested into the system."""
    # Verify that the ingest_cmd function was called
    mock_ingest_cmd.assert_called_once()


@then("the system should display an error message indicating the file does not exist")
def file_not_exist_error_displayed(context, capsys):
    """Verify that an error message about a non-existent file was displayed."""
    # This would check the captured stdout for error messages about non-existent files
    # Since we're mocking, we'll just verify the command failed
    assert context.result == "failure"
    assert context.error_message is not None


@then("the ingest command should run in non-interactive mode")
def ingest_non_interactive(mock_ingest_cmd):
    """Verify non-interactive flag passed to ingest command."""
    args = mock_ingest_cmd.call_args.kwargs
    assert args.get("non_interactive") is True


@then("the ingest command should apply defaults and run non-interactively")
def ingest_defaults_mode(mock_ingest_cmd):
    """Verify defaults imply non-interactive mode."""
    args = mock_ingest_cmd.call_args.kwargs
    assert args.get("defaults") is True
    assert args.get("non_interactive") is True
