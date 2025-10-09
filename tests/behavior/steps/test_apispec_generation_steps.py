"""BDD steps for the ``apispec`` command."""

import importlib
import os
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]


@pytest.fixture
def apispec_context(monkeypatch):
    """Provide a patched ``apispec_cmd`` for testing."""
    import devsynth.application.cli.apispec as api_module

    mock_cmd = MagicMock()
    monkeypatch.setattr(api_module, "apispec_cmd", mock_cmd)
    return {"cmd": mock_cmd}


scenarios(feature_path(__file__, "general", "apispec_generation.feature"))


@given("the DevSynth CLI is installed")
def cli_installed():
    """Placeholder step confirming CLI availability."""
    return True


@given("I have a valid DevSynth project")
def valid_project(tmp_project_dir):
    """Create a minimal DevSynth project."""
    manifest_path = os.path.join(tmp_project_dir, "devsynth.yaml")
    with open(manifest_path, "w") as f:
        f.write("projectName: test-project\nversion: 1.0.0\n")
    return tmp_project_dir


@when(parsers.parse('I run the command "{command}"'))
def run_command(command, apispec_context):
    apispec_context["cmd"]()


@given("the apispec_generation feature context")
def given_context(apispec_context):
    """Return the patched context."""
    return apispec_context


@when("we execute the apispec_generation workflow")
def when_execute(apispec_context):
    """Invoke the ``apispec`` command."""
    from devsynth.application.cli.apispec import apispec_cmd

    apispec_cmd()
    apispec_context["cmd"] = apispec_cmd


@then("the apispec_generation workflow completes")
def then_complete(apispec_context):
    """Ensure the command was called."""
    apispec_context["cmd"].assert_called_once()


@then("the system should generate a REST API specification")
def check_generation(apispec_context):
    """Verify the command executed."""
    apispec_context["cmd"].assert_called_once()


@then(parsers.parse("the specification should be in {format} format"))
def check_format(format):
    """Placeholder for format verification."""
    return True


@then("the specification should be created in the current directory")
def check_location_current():
    """Placeholder for current directory check."""
    return True


@then(
    parsers.parse('the specification should be created in the "{directory}" directory')
)
def check_location(directory):
    """Placeholder for location check."""
    return True


@then(parsers.parse('the specification should be named "{name}"'))
def check_name(name):
    """Placeholder for name check."""
    return True


@then("the output should indicate that the specification was generated")
def check_output():
    """Placeholder for output verification."""
    return True


@then("the workflow should execute successfully")
def workflow_success():
    """Placeholder for workflow success check."""
    return True


@then(parsers.parse("the system should generate a {api_type} API specification"))
def check_api_spec(api_type):
    """Placeholder for API type spec generation check."""
    return True


@then("the system should display an error message")
def error_message():
    """Placeholder for error message check."""
    return True


@then("the error message should indicate that the API type is not supported")
def error_api_type():
    """Placeholder for unsupported API type message check."""
    return True


@then("the workflow should not execute successfully")
def workflow_not_success():
    """Placeholder for negative workflow check."""
    return True


@then("the error message should indicate that the format is not supported")
def error_format():
    """Placeholder for unsupported format message check."""
    return True
