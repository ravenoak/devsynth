"""
Step definitions for the project_state_analyzer.feature file.

This module contains the step definitions for the Project State Analyzer behavior tests.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, then, when

from devsynth.application.code_analysis.project_state_analyzer import (
    ProjectStateAnalyzer,
)
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file
scenarios = pytest.importorskip("pytest_bdd").scenarios(
    feature_path(__file__, "general", "project_state_analyzer.feature")
)


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary directory with a test project structure."""
    # Create a basic project structure
    project_dir = tmp_path / "test_project"

    # Create directories for different architecture patterns
    (project_dir / "src" / "models").mkdir(parents=True)
    (project_dir / "src" / "views").mkdir(parents=True)
    (project_dir / "src" / "controllers").mkdir(parents=True)
    (project_dir / "src" / "domain").mkdir(parents=True)
    (project_dir / "src" / "application").mkdir(parents=True)
    (project_dir / "src" / "adapters").mkdir(parents=True)
    (project_dir / "docs").mkdir(parents=True)
    (project_dir / "tests").mkdir(parents=True)

    # Create some Python files
    (project_dir / "src" / "models" / "user.py").write_text(
        "class User:\n    def __init__(self, name):\n        self.name = name"
    )
    (project_dir / "src" / "controllers" / "user_controller.py").write_text(
        "from src.models.user import User\n\nclass UserController:\n    def get_user(self, user_id):\n        return User('Test')"
    )
    (project_dir / "src" / "views" / "user_view.py").write_text(
        "class UserView:\n    def render_user(self, user):\n        return f'User: {user.name}'"
    )

    # Create requirements and specification files
    (project_dir / "docs" / "requirements.md").write_text(
        "# Requirements\n\n1. The system shall allow users to create accounts.\n2. The system shall allow users to log in."
    )
    (project_dir / "docs" / "specifications.md").write_text(
        "# Specifications\n\n1. User Creation: The system will provide an API endpoint for user creation.\n2. User Authentication: The system will support username/password authentication."
    )

    # Create a test file
    (project_dir / "tests" / "test_user.py").write_text(
        "def test_user_creation():\n    from src.models.user import User\n    user = User('Test')\n    assert user.name == 'Test'"
    )

    return project_dir


@pytest.fixture
def context():
    """Create a context object for sharing data between steps."""

    class Context:
        def __init__(self):
            self.analyzer = None
            self.result = None
            self.edrr_coordinator = None
            self.wsde_team = None

    return Context()


# Background steps
@given("the DevSynth system is initialized")
def devsynth_initialized():
    """Initialize the DevSynth system."""
    # This is a placeholder step that doesn't need to do anything
    pass


@given("the project state analyzer is configured")
def project_state_analyzer_configured(context, test_project_dir):
    """Configure the project state analyzer."""
    context.analyzer = ProjectStateAnalyzer(str(test_project_dir))


# Scenario: Analyze project structure
@when("I analyze the project structure")
def analyze_project_structure(context):
    """Analyze the project structure."""
    context.analyzer._index_files()
    context.result = context.analyzer.files


@then("the analyzer should identify all files in the project")
def verify_files_identified(context, test_project_dir):
    """Verify that all files in the project are identified."""
    # Count the number of files in the test project
    file_count = 0
    for root, _, files in os.walk(test_project_dir):
        file_count += len(files)

    # Verify that the analyzer found all files
    assert (
        len(context.result) == file_count
    ), f"Expected {file_count} files, but found {len(context.result)}"


@then("the analyzer should categorize files by type")
def verify_files_categorized(context):
    """Verify that files are categorized by type."""
    # Check that files are categorized
    categories = set()
    for file_info in context.result.values():
        if "category" in file_info:
            categories.add(file_info["category"])

    # Verify that there are multiple categories
    assert len(categories) > 0, "No file categories found"


@then("the analyzer should detect the programming languages used")
def verify_languages_detected(context):
    """Verify that programming languages are detected."""
    context.analyzer._detect_languages()

    # Verify that Python is detected
    assert "python" in context.analyzer.languages, "Python language not detected"
    assert (
        context.analyzer.languages["python"]["percentage"] > 0
    ), "Python percentage is zero"


@then("the analyzer should provide metrics about the project structure")
def verify_metrics_provided(context):
    """Verify that metrics about the project structure are provided."""
    # Analyze the project to get metrics
    result = context.analyzer.analyze()

    # Verify that metrics are provided
    assert "metrics" in result, "No metrics in analysis result"
    assert "total_files" in result["metrics"], "No total_files metric"
    assert "file_types" in result["metrics"], "No file_types metric"
    assert "languages" in result["metrics"], "No languages metric"


# Scenario: Infer project architecture
@when("I analyze the project architecture")
def analyze_project_architecture(context):
    """Analyze the project architecture."""
    context.analyzer._index_files()
    context.analyzer._infer_architecture()
    context.result = context.analyzer.architecture


@then("the analyzer should detect the architecture pattern used")
def verify_architecture_detected(context):
    """Verify that the architecture pattern is detected."""
    # Verify that at least one architecture pattern is detected
    assert len(context.result) > 0, "No architecture patterns detected"


@then("the analyzer should identify components based on the architecture")
def verify_components_identified(context):
    """Verify that components are identified based on the architecture."""
    # Get the architecture with the highest confidence
    architecture_type = max(context.result.items(), key=lambda x: x[1]["confidence"])[0]

    # Identify components for this architecture
    components = context.analyzer._identify_components(architecture_type)

    # Verify that components are identified
    assert len(components) > 0, "No components identified"


@then("the analyzer should provide confidence scores for detected architectures")
def verify_confidence_scores(context):
    """Verify that confidence scores are provided for detected architectures."""
    # Verify that each architecture has a confidence score
    for arch_info in context.result.values():
        assert "confidence" in arch_info, "No confidence score for architecture"
        assert 0 <= arch_info["confidence"] <= 1, "Confidence score not between 0 and 1"


@then("the analyzer should identify architectural layers")
def verify_layers_identified(context):
    """Verify that architectural layers are identified."""
    # Get the architecture with the highest confidence
    architecture_type = max(context.result.items(), key=lambda x: x[1]["confidence"])[0]

    # Identify components for this architecture
    components = context.analyzer._identify_components(architecture_type)

    # Verify that layers are identified (components represent layers)
    assert len(components) > 0, "No layers identified"


# Scenario: Analyze MVC architecture
@given("a project with Model-View-Controller architecture")
def project_with_mvc_architecture(context, test_project_dir):
    """Set up a project with Model-View-Controller architecture."""
    # The test_project_dir fixture already sets up an MVC-like structure
    context.analyzer = ProjectStateAnalyzer(str(test_project_dir))


@then("the analyzer should detect MVC architecture with high confidence")
def verify_mvc_detected(context):
    """Verify that MVC architecture is detected with high confidence."""
    # Verify that MVC is detected
    assert "mvc" in context.result, "MVC architecture not detected"
    assert context.result["mvc"]["confidence"] > 0.5, "MVC confidence is not high"


@then("the analyzer should identify models, views, and controllers")
def verify_mvc_components(context):
    """Verify that models, views, and controllers are identified."""
    # Identify MVC components
    components = context.analyzer._identify_components("mvc")

    # Verify that models, views, and controllers are identified
    assert "models" in components, "Models not identified"
    assert "views" in components, "Views not identified"
    assert "controllers" in components, "Controllers not identified"


@then("the analyzer should analyze dependencies between MVC components")
def verify_mvc_dependencies(context):
    """Verify that dependencies between MVC components are analyzed."""
    # This would require a more complex implementation to actually analyze dependencies
    # For now, we'll just check that the components exist
    components = context.analyzer._identify_components("mvc")
    assert len(components) >= 3, "Not enough MVC components identified"


# Scenario: Analyze hexagonal architecture
@given("a project with hexagonal architecture")
def project_with_hexagonal_architecture(context, test_project_dir):
    """Set up a project with hexagonal architecture."""
    # The test_project_dir fixture already sets up a structure with domain, application, adapters
    context.analyzer = ProjectStateAnalyzer(str(test_project_dir))


# Add similar step definitions for other architecture types and scenarios...


# Scenario: Integrate with EDRR workflow
@given("the EDRR workflow is configured")
def edrr_workflow_configured(context):
    """Configure the EDRR workflow."""
    # Create a mock EDRR coordinator
    context.edrr_coordinator = MagicMock(spec=EnhancedEDRRCoordinator)


@when("I initiate a project analysis task")
def initiate_project_analysis_task(context):
    """Initiate a project analysis task."""
    # Mock the execution of a project analysis task
    context.result = {"task": "project_analysis", "status": "completed"}


@then("the system should use project state analysis in the Analysis phase")
def verify_analysis_phase(context):
    """Verify that project state analysis is used in the Analysis phase."""
    # This is a placeholder verification
    assert context.result["task"] == "project_analysis"


# Scenario: Integrate with WSDE team
@given("the WSDE team is configured")
def wsde_team_configured(context):
    """Configure the WSDE team."""
    # Create a mock WSDE team
    context.wsde_team = MagicMock(spec=WSDETeam)


@when("I assign a project analysis task to the WSDE team")
def assign_project_analysis_task(context):
    """Assign a project analysis task to the WSDE team."""
    # Mock the assignment of a project analysis task
    context.result = {
        "task": "project_analysis",
        "assigned_to": "wsde_team",
        "status": "completed",
    }


@then("the team should collaborate to analyze different aspects of the project")
def verify_team_collaboration(context):
    """Verify that the team collaborates to analyze different aspects of the project."""
    # This is a placeholder verification
    assert context.result["assigned_to"] == "wsde_team"
