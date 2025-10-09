from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.code_analysis.project_state_analysis import (
    analyze_project_state,
)
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "project_state_analysis.feature"))


@pytest.fixture
def context():
    class Context:
        project_path: str | None = None
        analysis: dict | None = None

    return Context()


@given("a project with requirements, specifications, tests, and code")
def sample_project(tmp_path: Path, context):
    project_dir = tmp_path / "sample_project"
    (project_dir / "docs").mkdir(parents=True)
    (project_dir / "tests").mkdir()
    (project_dir / "src").mkdir()

    (project_dir / "docs" / "requirements.md").write_text(
        "# Requirements\n\n1. The system shall exist."
    )
    (project_dir / "docs" / "specifications.md").write_text(
        "# Specifications\n\n1. Implement the system."
    )
    (project_dir / "src" / "main.py").write_text("def main():\n    return True\n")
    (project_dir / "tests" / "test_main.py").write_text(
        "def sample_main():\n    assert True\n"
    )

    context.project_path = str(project_dir)


@when("I analyze the project state")
def analyze_state(context):
    context.analysis = analyze_project_state(context.project_path)


@then("the analysis reports counts for requirements, specifications, tests, and code")
def verify_counts(context):
    result = context.analysis
    assert result["requirements_count"] > 0
    assert result["specifications_count"] > 0
    assert result["test_count"] > 0
    assert result["code_count"] > 0


@then("the analysis includes a health score between 0 and 10")
def verify_health_score(context):
    score = context.analysis["health_score"]
    assert 0 <= score <= 10
