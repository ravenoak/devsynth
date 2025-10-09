"""Steps for the validate manifest command feature."""

from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then

from tests.behavior.feature_paths import feature_path

# Reuse generic CLI step implementations so we don't duplicate behavior.
from .cli_commands_steps import *  # noqa: F401,F403 - re-export CLI steps
from .test_analyze_commands_steps import check_error_message  # noqa: F401

pytestmark = [pytest.mark.fast]


@given("no manifest file exists at the provided path")
def missing_manifest(tmp_path: Path, command_context):
    """Provide a path to a nonexistent manifest file for error handling."""

    path = tmp_path / "missing.json"
    command_context["manifest_path"] = path
    return path


scenarios(feature_path(__file__, "general", "validate_manifest_command.feature"))


@then("the output should indicate the project configuration is valid")
def manifest_valid(command_context):
    """Check for a success message from validate-manifest."""
    output = command_context.get("output", "")
    assert "Project configuration is valid" in output
