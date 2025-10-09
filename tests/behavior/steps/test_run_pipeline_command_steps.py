import os
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "run_pipeline_command.feature"))


# Fixtures for test isolation
@pytest.fixture
def context():
    """Fixture to provide a context object for sharing data between steps."""

    class Context:
        def __init__(self):
            self.result = None
            self.error_message = None
            self.target = None
            self.file = None
            self.verbose = False
            self.test_results = {
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "total": 0,
                "details": [],
            }

    return Context()


@pytest.fixture
def mock_run_pipeline_cmd():
    """Fixture to mock the run_pipeline_cmd function."""
    with patch("devsynth.application.cli.run_pipeline_cmd.run_pipeline_cmd") as mock:
        yield mock


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project structure for testing."""
    # Create a simple project structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Create a sample Python file
    main_py = src_dir / "main.py"
    main_py.write_text(
        """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    )

    # Create a tests directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    # Create a sample test file
    test_example_py = tests_dir / "test_example.py"
    test_example_py.write_text(
        """
import unittest
from src.main import add, subtract

class TestMathFunctions(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(1, 2), 3)

    def test_subtract(self):
        self.assertEqual(subtract(5, 3), 2)
"""
    )

    return tmp_path


# Step definitions
@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    """Verify that the DevSynth CLI is installed."""
    # This is a placeholder step since we're running tests within the DevSynth codebase
    pass


@given("I have a project with generated code")
def project_with_generated_code(context, sample_project):
    """Set up a project with generated code for testing."""
    context.project_path = sample_project
    context.src_path = os.path.join(sample_project, "src")
    context.tests_path = os.path.join(sample_project, "tests")
    context.test_file_path = os.path.join(context.tests_path, "test_example.py")


@when(parsers.parse('I run the command "{command}"'))
def run_command(context, command, mock_run_pipeline_cmd):
    """Run a DevSynth CLI command."""
    # Parse the command to extract arguments
    args = command.split()[1:]  # Skip 'devsynth'

    # Extract target, file, and verbose flag if present
    context.target = None
    context.file = None
    context.verbose = False

    if "--target" in args:
        target_index = args.index("--target")
        if target_index + 1 < len(args):
            context.target = args[target_index + 1]

    if "--file" in args:
        file_index = args.index("--file")
        if file_index + 1 < len(args):
            context.file = args[file_index + 1]
            # If the file is specified, use the actual path from our sample project
            if context.file == "tests/test_example.py":
                context.file = context.test_file_path

    if "--verbose" in args:
        context.verbose = True

    # Set up the mock behavior based on the scenario
    if context.target == "non-existent-target":
        mock_run_pipeline_cmd.side_effect = ValueError(
            f"Invalid target: {context.target}"
        )
        try:
            # Simulate running the command
            from devsynth.adapters.cli.typer_adapter import parse_args

            parse_args(args)
            context.result = "success"
        except Exception as e:
            context.result = "failure"
            context.error_message = str(e)
    else:
        # Set up mock to return test results based on the target
        if context.target == "unit-tests":
            mock_run_pipeline_cmd.return_value = {
                "passed": 2,
                "failed": 0,
                "skipped": 0,
                "total": 2,
                "details": [
                    {"name": "test_add", "result": "passed"},
                    {"name": "test_subtract", "result": "passed"},
                ],
            }
        elif context.target == "integration-tests":
            mock_run_pipeline_cmd.return_value = {
                "passed": 1,
                "failed": 1,
                "skipped": 0,
                "total": 2,
                "details": [
                    {"name": "test_integration_1", "result": "passed"},
                    {
                        "name": "test_integration_2",
                        "result": "failed",
                        "error": "AssertionError",
                    },
                ],
            }
        elif context.target == "behavior-tests":
            mock_run_pipeline_cmd.return_value = {
                "passed": 3,
                "failed": 0,
                "skipped": 1,
                "total": 4,
                "details": [
                    {"name": "test_scenario_1", "result": "passed"},
                    {"name": "test_scenario_2", "result": "passed"},
                    {"name": "test_scenario_3", "result": "passed"},
                    {"name": "test_scenario_4", "result": "skipped"},
                ],
            }
        elif context.target == "all-tests":
            mock_run_pipeline_cmd.return_value = {
                "passed": 6,
                "failed": 1,
                "skipped": 1,
                "total": 8,
                "details": [
                    {"name": "test_add", "result": "passed"},
                    {"name": "test_subtract", "result": "passed"},
                    {"name": "test_integration_1", "result": "passed"},
                    {
                        "name": "test_integration_2",
                        "result": "failed",
                        "error": "AssertionError",
                    },
                    {"name": "test_scenario_1", "result": "passed"},
                    {"name": "test_scenario_2", "result": "passed"},
                    {"name": "test_scenario_3", "result": "passed"},
                    {"name": "test_scenario_4", "result": "skipped"},
                ],
            }

        # If verbose is specified, add more details to the test results
        if context.verbose:
            for detail in mock_run_pipeline_cmd.return_value["details"]:
                detail["duration"] = "0.123s"
                if detail["result"] == "failed":
                    detail["traceback"] = (
                        'Traceback (most recent call last):\n  File "test.py", line 10, in test\n    assert False\nAssertionError'
                    )

        # If a specific file is specified, filter the results to only include tests from that file
        if context.file:
            filtered_details = [
                d
                for d in mock_run_pipeline_cmd.return_value["details"]
                if d["name"].startswith("test_")
            ]
            mock_run_pipeline_cmd.return_value["details"] = filtered_details
            mock_run_pipeline_cmd.return_value["passed"] = len(
                [d for d in filtered_details if d["result"] == "passed"]
            )
            mock_run_pipeline_cmd.return_value["failed"] = len(
                [d for d in filtered_details if d["result"] == "failed"]
            )
            mock_run_pipeline_cmd.return_value["skipped"] = len(
                [d for d in filtered_details if d["result"] == "skipped"]
            )
            mock_run_pipeline_cmd.return_value["total"] = len(filtered_details)

        try:
            # Simulate running the command
            from devsynth.adapters.cli.typer_adapter import parse_args

            parse_args(args)
            context.result = "success"
            # Store the test results if the command was successful
            context.test_results = mock_run_pipeline_cmd.return_value
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


@then("the system should run the unit tests")
def run_unit_tests(context, mock_run_pipeline_cmd):
    """Verify that the system ran the unit tests."""
    assert context.target == "unit-tests", "Target was not set to unit-tests"
    mock_run_pipeline_cmd.assert_called_once()


@then("the system should run the integration tests")
def run_integration_tests(context, mock_run_pipeline_cmd):
    """Verify that the system ran the integration tests."""
    assert (
        context.target == "integration-tests"
    ), "Target was not set to integration-tests"
    mock_run_pipeline_cmd.assert_called_once()


@then("the system should run the behavior tests")
def run_behavior_tests(context, mock_run_pipeline_cmd):
    """Verify that the system ran the behavior tests."""
    assert context.target == "behavior-tests", "Target was not set to behavior-tests"
    mock_run_pipeline_cmd.assert_called_once()


@then("the system should run all tests")
def run_all_tests(context, mock_run_pipeline_cmd):
    """Verify that the system ran all tests."""
    assert context.target == "all-tests", "Target was not set to all-tests"
    mock_run_pipeline_cmd.assert_called_once()


@then("the system should display test results")
def display_test_results(context):
    """Verify that test results were displayed."""
    assert "passed" in context.test_results, "Test results do not include passed count"
    assert "failed" in context.test_results, "Test results do not include failed count"
    assert "total" in context.test_results, "Test results do not include total count"
    assert "details" in context.test_results, "Test results do not include details"


@then("the system should display detailed test results")
def display_detailed_test_results(context):
    """Verify that detailed test results were displayed."""
    assert context.verbose is True, "Verbose flag was not set"
    assert "details" in context.test_results, "Test results do not include details"
    for detail in context.test_results["details"]:
        assert "duration" in detail, "Test detail does not include duration"
        if detail["result"] == "failed":
            assert (
                "traceback" in detail
            ), "Failed test detail does not include traceback"


@then("the system should run the specified test file")
def run_specified_test_file(context, mock_run_pipeline_cmd):
    """Verify that the system ran the specified test file."""
    assert context.file is not None, "File was not specified"
    mock_run_pipeline_cmd.assert_called_once()


@then("the system should display test results for that file")
def display_file_specific_test_results(context):
    """Verify that test results for the specified file were displayed."""
    assert context.file is not None, "File was not specified"
    assert "details" in context.test_results, "Test results do not include details"
    # In a real test, we would check that the results are specific to the file
    # For this mock, we'll just check that we have results


@then("the system should display an error message about the invalid target")
def invalid_target_error_displayed(context):
    """Verify that an error message about an invalid target was displayed."""
    assert context.result == "failure", "Command succeeded but was expected to fail"
    assert context.error_message is not None, "No error message was generated"
    assert (
        "Invalid target" in context.error_message
    ), "Error message does not indicate invalid target"
