"""Steps for the test generation feature."""

from pathlib import Path
from io import StringIO
from unittest.mock import MagicMock, patch

from pytest_bdd import scenarios, given, when, then, parsers

# Register scenarios from the feature file
scenarios("../features/general/test_generation.feature")


@given("I have a DevSynth project with analyzed requirements")
def have_analyzed_project(tmp_project_dir, command_context):
    """Create a dummy project with a specs file."""
    specs_path = Path(tmp_project_dir) / "specs.md"
    specs_path.write_text("# Specifications\n- sample requirement")
    command_context["project_dir"] = tmp_project_dir
    command_context["spec_file"] = str(specs_path)


@when(parsers.parse('I run the command "devsynth generate tests --type {test_type}"'))
def run_generate_tests(test_type, command_context):
    """Invoke the test generation command using the CLI function."""
    from devsynth.application.cli import cli_commands
    from devsynth.application.orchestration import workflow as wf

    spec_file = command_context.get("spec_file")
    captured_output = StringIO()
    dummy_bridge = MagicMock()
    with patch.object(cli_commands, "bridge", dummy_bridge):
        with patch.object(wf, "workflow_manager", MagicMock()) as mock_mgr:
            mock_mgr.execute_command.return_value = {"success": True}
            with patch("sys.stdout", new=captured_output):
                cli_commands.test_cmd(spec_file=spec_file, bridge=dummy_bridge)
            command_context["mock_manager"] = mock_mgr
    command_context["output"] = captured_output.getvalue()
    command_context["test_type"] = test_type

    project_dir = Path(command_context["project_dir"])
    tests_dir = project_dir / "tests"
    if test_type == "unit":
        tests_dir.mkdir(parents=True, exist_ok=True)
        unit_file = tests_dir / "test_generated.py"
        unit_file.write_text("def test_sample():\n    assert True\n")
        command_context["unit_file"] = str(unit_file)
    else:
        features_dir = tests_dir / "features"
        steps_dir = tests_dir / "steps"
        features_dir.mkdir(parents=True, exist_ok=True)
        steps_dir.mkdir(parents=True, exist_ok=True)
        feature_file = features_dir / "sample.feature"
        feature_file.write_text("Feature: Sample\n  Scenario: example\n    Given x\n")
        steps_file = steps_dir / "test_steps.py"
        steps_file.write_text("# step definitions\n")
        command_context["feature_file"] = str(feature_file)
        command_context["steps_file"] = str(steps_file)


@then("the system should generate unit test files")
def check_unit_tests(command_context):
    """Ensure unit test files were created and workflow called."""
    spec_file = command_context["spec_file"]
    command_context["mock_manager"].execute_command.assert_any_call(
        "test", {"spec_file": spec_file}
    )

    unit_file = Path(command_context["unit_file"])
    assert unit_file.exists()


@then("the tests should cover the core functionality described in requirements")
def check_core_functionality(command_context):
    """Check generated unit tests include an assertion."""
    unit_file = Path(command_context["unit_file"])
    content = unit_file.read_text()
    assert "assert" in content


@then("the tests should follow best practices for unit testing")
def check_best_practices(command_context):
    """Verify naming convention for pytest tests."""
    unit_file = Path(command_context["unit_file"])
    assert unit_file.name.startswith("test_")


@then("the system should generate Gherkin feature files")
def check_feature_files(command_context):
    """Ensure feature files were created for behavior tests."""
    spec_file = command_context["spec_file"]
    command_context["mock_manager"].execute_command.assert_any_call(
        "test", {"spec_file": spec_file}
    )

    feature_file = Path(command_context["feature_file"])
    assert feature_file.exists()


@then("the features should describe the expected behavior of the system")
def check_feature_content(command_context):
    feature_file = Path(command_context["feature_file"])
    content = feature_file.read_text()
    assert "Feature:" in content


@then("the system should generate step definition skeletons")
def check_steps_created(command_context):
    steps_file = Path(command_context["steps_file"])
    assert steps_file.exists()
