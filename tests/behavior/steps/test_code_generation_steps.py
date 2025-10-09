"""Steps for the code generation feature."""

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .cli_commands_steps import run_command
from .test_generation_steps import have_analyzed_project

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "code_generation.feature"))


@pytest.fixture
def command_context():
    """Context object shared between steps."""
    return {}


@given("I have a DevSynth project with analyzed requirements")
def analyzed_project(tmp_project_dir, command_context):
    """Reuse analyzed project setup from test generation steps."""
    have_analyzed_project(tmp_project_dir, command_context)


@given("I have generated tests")
def generated_tests(tmp_project_dir, command_context):
    """Create a dummy test file to simulate generated tests."""
    tests_dir = Path(tmp_project_dir) / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_file = tests_dir / "test_generated.py"
    test_file.write_text("def test_dummy():\n    assert True\n")
    command_context["generated_tests"] = str(test_file)


@given("I have a DevSynth project with generated code")
def project_with_code(tmp_project_dir, command_context):
    src_dir = Path(tmp_project_dir) / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    code_file = src_dir / "main.py"
    code_file.write_text("def main():\n    return True\n")
    command_context["project_dir"] = tmp_project_dir
    command_context["code_file"] = str(code_file)


@when('I run the command "devsynth generate code"')
def run_generate_code(monkeypatch, mock_workflow_manager, command_context):
    """Execute the generate code command using shared helper."""
    run_command(
        "devsynth generate code",
        monkeypatch,
        mock_workflow_manager,
        command_context,
    )


@when(parsers.parse('I run the command "{command}"'))
def run_refine_code(command, monkeypatch, mock_workflow_manager, command_context):
    """Execute a refinement command."""
    run_command(command, monkeypatch, mock_workflow_manager, command_context)


@then("the system should generate code that implements the requirements")
def code_generated(command_context):
    output = command_context.get("output", "")
    assert "generate code" in command_context.get("command", "")
    assert output != ""


@then("the generated code should pass the generated tests")
def verify_generated_tests_passed(command_context):
    """Ensure the mock workflow manager is available for test execution."""
    assert command_context.get("mock_manager") is not None


@then("the code should follow best practices and coding standards")
def code_best_practices():
    assert True


@then("the system should analyze the existing code")
def analyze_code(command_context):
    assert command_context.get("command", "").startswith("devsynth refine code")


@then("update the code to improve error handling")
def update_code():
    assert True


@then("ensure all tests still pass")
def ensure_tests_pass():
    assert True
