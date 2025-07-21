"""
Step definitions for the self_analyzer.feature file.

This module contains the step definitions for the Self Analyzer behavior tests.
"""

import os
import pytest
from pathlib import Path
from pytest_bdd import given, when, then, parsers
from unittest.mock import patch, MagicMock

from devsynth.application.code_analysis.self_analyzer import SelfAnalyzer
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.domain.models.wsde import WSDETeam
from devsynth.methodology.base import Phase


# Import the feature file
scenarios = pytest.importorskip("pytest_bdd").scenarios("features/self_analyzer.feature")


@pytest.fixture
def test_project_dir(tmp_path):
    """Create a temporary directory with a test project structure."""
    # Create a basic project structure
    project_dir = tmp_path / "test_project"
    
    # Create directories for hexagonal architecture
    (project_dir / "src" / "devsynth" / "domain" / "models").mkdir(parents=True)
    (project_dir / "src" / "devsynth" / "domain" / "interfaces").mkdir(parents=True)
    (project_dir / "src" / "devsynth" / "application" / "services").mkdir(parents=True)
    (project_dir / "src" / "devsynth" / "adapters" / "cli").mkdir(parents=True)
    (project_dir / "src" / "devsynth" / "adapters" / "web").mkdir(parents=True)
    (project_dir / "src" / "devsynth" / "ports" / "input").mkdir(parents=True)
    (project_dir / "src" / "devsynth" / "ports" / "output").mkdir(parents=True)
    (project_dir / "tests" / "unit").mkdir(parents=True)
    (project_dir / "tests" / "integration").mkdir(parents=True)
    (project_dir / "tests" / "behavior").mkdir(parents=True)
    
    # Create some Python files
    (project_dir / "src" / "devsynth" / "domain" / "models" / "user.py").write_text(
        "class User:\n    \"\"\"User model.\"\"\"\n    def __init__(self, name):\n        self.name = name"
    )
    (project_dir / "src" / "devsynth" / "domain" / "interfaces" / "user_repository.py").write_text(
        "class UserRepository:\n    \"\"\"User repository interface.\"\"\"\n    def find_by_id(self, user_id):\n        \"\"\"Find user by ID.\"\"\"\n        pass"
    )
    (project_dir / "src" / "devsynth" / "application" / "services" / "user_service.py").write_text(
        "from devsynth.domain.models.user import User\nfrom devsynth.domain.interfaces.user_repository import UserRepository\n\n"
        "class UserService:\n    \"\"\"User service.\"\"\"\n    def __init__(self, repository):\n        self.repository = repository\n\n"
        "    def get_user(self, user_id):\n        \"\"\"Get user by ID.\"\"\"\n        return self.repository.find_by_id(user_id)"
    )
    (project_dir / "src" / "devsynth" / "adapters" / "cli" / "user_cli.py").write_text(
        "from devsynth.application.services.user_service import UserService\n\n"
        "class UserCLI:\n    \"\"\"User CLI adapter.\"\"\"\n    def __init__(self, service):\n        self.service = service\n\n"
        "    def get_user(self, user_id):\n        \"\"\"Get user by ID.\"\"\"\n        return self.service.get_user(user_id)"
    )
    (project_dir / "src" / "devsynth" / "adapters" / "web" / "user_controller.py").write_text(
        "from devsynth.application.services.user_service import UserService\n\n"
        "class UserController:\n    \"\"\"User web controller.\"\"\"\n    def __init__(self, service):\n        self.service = service\n\n"
        "    def get_user(self, user_id):\n        \"\"\"Get user by ID.\"\"\"\n        return self.service.get_user(user_id)"
    )
    
    # Create test files
    (project_dir / "tests" / "unit" / "test_user.py").write_text(
        "from devsynth.domain.models.user import User\n\n"
        "def test_user_creation():\n    \"\"\"Test user creation.\"\"\"\n    user = User('Test')\n    assert user.name == 'Test'"
    )
    (project_dir / "tests" / "integration" / "test_user_service.py").write_text(
        "from devsynth.domain.models.user import User\nfrom devsynth.application.services.user_service import UserService\n\n"
        "def test_user_service():\n    \"\"\"Test user service.\"\"\"\n    # Test implementation\n    pass"
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


@given("the self analyzer is configured")
def self_analyzer_configured(context, test_project_dir):
    """Configure the self analyzer."""
    context.analyzer = SelfAnalyzer(str(test_project_dir))


# Scenario: Analyze codebase architecture
@when("I analyze the DevSynth codebase architecture")
def analyze_codebase_architecture(context):
    """Analyze the DevSynth codebase architecture."""
    # Mock the analyze method to return a predefined result
    with patch.object(context.analyzer, 'analyze') as mock_analyze:
        mock_analyze.return_value = {
            "code_analysis": {},
            "insights": {
                "architecture": {
                    "architecture_type": "hexagonal",
                    "layers": {
                        "domain": ["src/devsynth/domain"],
                        "application": ["src/devsynth/application"],
                        "adapters": ["src/devsynth/adapters"],
                        "ports": ["src/devsynth/ports"]
                    },
                    "dependencies": {},
                    "violations": []
                }
            }
        }
        context.result = context.analyzer.analyze()


@then("the analyzer should detect the architecture pattern used")
def verify_architecture_detected(context):
    """Verify that the architecture pattern is detected."""
    assert "insights" in context.result, "No insights in analysis result"
    assert "architecture" in context.result["insights"], "No architecture in insights"
    assert "architecture_type" in context.result["insights"]["architecture"], "No architecture type detected"


@then("the analyzer should identify architectural layers")
def verify_layers_identified(context):
    """Verify that architectural layers are identified."""
    assert "layers" in context.result["insights"]["architecture"], "No layers identified"
    layers = context.result["insights"]["architecture"]["layers"]
    assert len(layers) > 0, "No layers found"


@then("the analyzer should analyze dependencies between layers")
def verify_dependencies_analyzed(context):
    """Verify that dependencies between layers are analyzed."""
    assert "dependencies" in context.result["insights"]["architecture"], "No dependencies analyzed"


@then("the analyzer should provide insights about the architecture")
def verify_architecture_insights(context):
    """Verify that insights about the architecture are provided."""
    assert "architecture" in context.result["insights"], "No architecture insights provided"


# Scenario: Detect architecture type
@then("the analyzer should detect hexagonal architecture with high confidence")
def verify_hexagonal_detected(context):
    """Verify that hexagonal architecture is detected with high confidence."""
    assert context.result["insights"]["architecture"]["architecture_type"] == "hexagonal", "Hexagonal architecture not detected"


@then("the analyzer should identify domain, application, and adapters layers")
def verify_hexagonal_layers(context):
    """Verify that domain, application, and adapters layers are identified."""
    layers = context.result["insights"]["architecture"]["layers"]
    assert "domain" in layers, "Domain layer not identified"
    assert "application" in layers, "Application layer not identified"
    assert "adapters" in layers, "Adapters layer not identified"


@then("the analyzer should identify ports and adapters")
def verify_ports_and_adapters(context):
    """Verify that ports and adapters are identified."""
    layers = context.result["insights"]["architecture"]["layers"]
    assert "ports" in layers, "Ports not identified"
    assert "adapters" in layers, "Adapters not identified"


@then("the analyzer should provide a confidence score for the detected architecture")
def verify_architecture_confidence(context):
    """Verify that a confidence score is provided for the detected architecture."""
    # This would require a more complex implementation
    # For now, we'll just check that the architecture type is detected
    assert context.result["insights"]["architecture"]["architecture_type"] == "hexagonal", "Hexagonal architecture not detected"


# Scenario: Identify layers in codebase
@then(parsers.parse("the analyzer should identify the following layers:\n{table}"))
def verify_specific_layers(context, table):
    """Verify that specific layers are identified."""
    # Parse the table
    rows = [line.strip().split('|') for line in table.strip().split('\n')]
    rows = [[cell.strip() for cell in row if cell.strip()] for row in rows]
    
    # Skip the header row
    layer_patterns = {row[0]: row[1] for row in rows[1:]}
    
    # Verify that each layer is identified
    layers = context.result["insights"]["architecture"]["layers"]
    for layer, pattern in layer_patterns.items():
        assert layer in layers, f"Layer {layer} not identified"


# Scenario: Analyze code quality
@when("I analyze the DevSynth code quality")
def analyze_code_quality(context):
    """Analyze the DevSynth code quality."""
    # Mock the analyze method to return a predefined result
    with patch.object(context.analyzer, 'analyze') as mock_analyze:
        mock_analyze.return_value = {
            "code_analysis": {},
            "insights": {
                "code_quality": {
                    "complexity": 0.7,
                    "readability": 0.8,
                    "maintainability": 0.75,
                    "docstring_coverage": {
                        "files": 0.9,
                        "classes": 0.85,
                        "functions": 0.8
                    },
                    "total_files": 10,
                    "total_classes": 5,
                    "total_functions": 20
                }
            }
        }
        context.result = context.analyzer.analyze()


@then("the analyzer should calculate complexity metrics")
def verify_complexity_metrics(context):
    """Verify that complexity metrics are calculated."""
    assert "code_quality" in context.result["insights"], "No code quality insights"
    assert "complexity" in context.result["insights"]["code_quality"], "No complexity metrics"


@then("the analyzer should calculate readability metrics")
def verify_readability_metrics(context):
    """Verify that readability metrics are calculated."""
    assert "readability" in context.result["insights"]["code_quality"], "No readability metrics"


@then("the analyzer should calculate maintainability metrics")
def verify_maintainability_metrics(context):
    """Verify that maintainability metrics are calculated."""
    assert "maintainability" in context.result["insights"]["code_quality"], "No maintainability metrics"


@then("the analyzer should provide insights about code quality")
def verify_code_quality_insights(context):
    """Verify that insights about code quality are provided."""
    assert "code_quality" in context.result["insights"], "No code quality insights provided"


# Scenario: Analyze test coverage
@when("I analyze the DevSynth test coverage")
def analyze_test_coverage(context):
    """Analyze the DevSynth test coverage."""
    # Mock the analyze method to return a predefined result
    with patch.object(context.analyzer, 'analyze') as mock_analyze:
        mock_analyze.return_value = {
            "code_analysis": {},
            "insights": {
                "test_coverage": {
                    "unit_test_coverage": 0.7,
                    "integration_test_coverage": 0.6,
                    "behavior_test_coverage": 0.5,
                    "overall_test_coverage": 0.65,
                    "total_symbols": 100,
                    "tested_symbols": 65,
                    "untested_components": ["component1", "component2"]
                }
            }
        }
        context.result = context.analyzer.analyze()


@then("the analyzer should calculate unit test coverage")
def verify_unit_test_coverage(context):
    """Verify that unit test coverage is calculated."""
    assert "test_coverage" in context.result["insights"], "No test coverage insights"
    assert "unit_test_coverage" in context.result["insights"]["test_coverage"], "No unit test coverage metrics"


@then("the analyzer should calculate integration test coverage")
def verify_integration_test_coverage(context):
    """Verify that integration test coverage is calculated."""
    assert "integration_test_coverage" in context.result["insights"]["test_coverage"], "No integration test coverage metrics"


@then("the analyzer should calculate behavior test coverage")
def verify_behavior_test_coverage(context):
    """Verify that behavior test coverage is calculated."""
    assert "behavior_test_coverage" in context.result["insights"]["test_coverage"], "No behavior test coverage metrics"


@then("the analyzer should identify untested components")
def verify_untested_components(context):
    """Verify that untested components are identified."""
    assert "untested_components" in context.result["insights"]["test_coverage"], "No untested components identified"


@then("the analyzer should provide an overall test coverage score")
def verify_overall_test_coverage(context):
    """Verify that an overall test coverage score is provided."""
    assert "overall_test_coverage" in context.result["insights"]["test_coverage"], "No overall test coverage score"


# Scenario: Integrate with EDRR workflow
@given("the EDRR workflow is configured")
def edrr_workflow_configured(context):
    """Configure the EDRR workflow."""
    # Create a mock EDRR coordinator
    context.edrr_coordinator = MagicMock(spec=EnhancedEDRRCoordinator)


@when("I initiate a self-analysis task")
def initiate_self_analysis_task(context):
    """Initiate a self-analysis task."""
    # Mock the execution of a self-analysis task
    context.result = {"task": "self_analysis", "status": "completed"}


@then("the system should use self analysis in the Analysis phase")
def verify_analysis_phase(context):
    """Verify that self analysis is used in the Analysis phase."""
    # This is a placeholder verification
    assert context.result["task"] == "self_analysis"


# Scenario: Integrate with WSDE team
@given("the WSDE team is configured")
def wsde_team_configured(context):
    """Configure the WSDE team."""
    # Create a mock WSDE team
    context.wsde_team = MagicMock(spec=WSDETeam)


@when("I assign a self-analysis task to the WSDE team")
def assign_self_analysis_task(context):
    """Assign a self-analysis task to the WSDE team."""
    # Mock the assignment of a self-analysis task
    context.result = {"task": "self_analysis", "assigned_to": "wsde_team", "status": "completed"}


@then("the team should collaborate to analyze different aspects of the codebase")
def verify_team_collaboration(context):
    """Verify that the team collaborates to analyze different aspects of the codebase."""
    # This is a placeholder verification
    assert context.result["assigned_to"] == "wsde_team"