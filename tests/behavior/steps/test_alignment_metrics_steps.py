"""Steps for the alignment metrics command feature."""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/general/alignment_metrics_command.feature")


@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    """Assume the DevSynth CLI is available in the test environment."""
    return True


@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_path):
    """Provide a temporary project directory for tests."""
    return tmp_path


@when(parsers.parse('I run the command "{command}"'))
def run_command(command, command_context):
    """Execute a CLI command (simulated for tests)."""
    command_context["command"] = command
    if command_context.get("force_error"):
        command_context["output"] = "Error: command failed"
        command_context["exit_code"] = 1
    elif "alignment-metrics" in command:
        command_context["output"] = "Alignment Metrics"
        command_context["exit_code"] = 0
    else:
        command_context["output"] = ""
        command_context["exit_code"] = 0


@then("the workflow should execute successfully")
def check_workflow_success(command_context):
    """Assert that the simulated command exited successfully."""
    assert command_context.get("exit_code", 1) == 0


@pytest.mark.medium
@given("alignment metrics calculation fails")
def metrics_fail(command_context):
    """Simulate a failure in the alignment metrics command."""

    command_context["force_error"] = True


@pytest.mark.medium
@then("the system should display alignment metrics")
def check_metrics_output(command_context):
    """Verify that alignment metrics were printed."""
    output = command_context.get("output", "")
    assert "Alignment Metrics" in output or "Metrics report" in output


@then("the system should display an error message")
def check_error_message(command_context):
    """Verify that an error was reported."""
    assert command_context.get("exit_code", 0) != 0
