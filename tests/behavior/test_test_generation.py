"""End-to-end tests for TestAgent integration test generation."""

from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.agents.test import TestAgent

pytestmark = [pytest.mark.fast]

FEATURE_FILE = (
    Path(__file__).parent / "features" / "test_generation" / "multi_module.feature"
)
scenarios(FEATURE_FILE)


@given("a project with multiple modules", target_fixture="project")
def setup_project(tmp_path):
    return {"output_dir": tmp_path, "modules": ["pkg1", "pkg2.utils"]}


@when("the TestAgent generates integration tests")
def generate_tests(project):
    agent = TestAgent()
    inputs = {
        "modules": project["modules"],
        "integration_output_dir": project["output_dir"],
    }
    project["result"] = agent.process(inputs)
    project["agent"] = agent


@then("tests are scaffolded for each module")
def check_scaffolded(project):
    output_dir = project["output_dir"]
    agent = project["agent"]
    result = project["result"]
    assert (output_dir / "pkg1" / "test_pkg1.py").exists()
    assert (output_dir / "pkg2" / "utils" / "test_utils.py").exists()
    assert "pkg1/test_pkg1.py" in result["integration_tests"]
    assert "pkg2/utils/test_utils.py" in result["integration_tests"]
    run_output = agent.run_generated_tests(output_dir)
    assert "2 passed" in run_output
