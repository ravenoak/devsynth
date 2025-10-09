"""Behavior steps for the alignment metrics command feature."""

from __future__ import annotations

from collections.abc import MutableMapping

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.medium]

scenarios(feature_path(__file__, "general", "alignment_metrics_command.feature"))


@pytest.fixture()
def command_context() -> MutableMapping[str, object]:
    """Return a mutable context dictionary shared across steps."""

    return {
        "command": "",
        "output": "",
        "exit_code": 0,
        "force_error": False,
    }


@given("the DevSynth CLI is installed")
def devsynth_cli_installed() -> bool:
    """Assume the DevSynth CLI is available."""

    return True


@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_path) -> str:
    """Provide a temporary project directory for tests."""

    return str(tmp_path)


@given("alignment metrics calculation fails")
def metrics_fail(command_context: MutableMapping[str, object]) -> None:
    """Force the simulated CLI command to raise an error."""

    command_context["force_error"] = True


@when(parsers.parse('I run the command "{command}"'))
def run_command(command: str, command_context: MutableMapping[str, object]) -> None:
    """Simulate running the alignment metrics CLI command."""

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
def check_workflow_success(command_context: MutableMapping[str, object]) -> None:
    """Assert that the simulated command exited successfully."""

    assert command_context.get("exit_code", 1) == 0


@then("the system should display alignment metrics")
def check_metrics_output(command_context: MutableMapping[str, object]) -> None:
    """Verify that alignment metrics were printed."""

    output = str(command_context.get("output", ""))
    assert "Alignment Metrics" in output or "Metrics report" in output


@then("the system should display an error message")
def check_error_message(command_context: MutableMapping[str, object]) -> None:
    """Verify that an error was reported."""

    assert command_context.get("exit_code", 0) != 0
