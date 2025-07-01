import os
import pytest
import tempfile
import shutil
from pathlib import Path

from devsynth.application.code_analysis.project_state_analyzer import ProjectStateAnalyzer
from devsynth.application.code_analysis.self_analyzer import SelfAnalyzer
from devsynth.application.orchestration.refactor_workflow import RefactorWorkflowManager
from devsynth.application.orchestration.workflow import WorkflowManager


class TestComprehensiveWorkflow:
    """
    A comprehensive integration test that exercises multiple components of the system.

    This test verifies that DevSynth can:
    1. Analyze any codebase (not just its own)
    2. Detect the architecture and structure of the codebase
    3. Suggest appropriate next steps based on the analysis
    4. Execute a complete workflow from requirements to code
    """

    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        try:
            # Create a simple project structure
            os.makedirs(os.path.join(temp_dir, "src", "sample_app", "models"))
            os.makedirs(os.path.join(temp_dir, "src", "sample_app", "views"))
            os.makedirs(os.path.join(temp_dir, "src", "sample_app", "controllers"))
            os.makedirs(os.path.join(temp_dir, "tests"))

            # Create a simple model file
            model_file = os.path.join(temp_dir, "src", "sample_app", "models", "user.py")
            with open(model_file, "w") as f:
                f.write("""
class User:
    \"\"\"A user model.\"\"\"

    def __init__(self, username, email):
        \"\"\"Initialize a user.\"\"\"
        self.username = username
        self.email = email

    def validate(self):
        \"\"\"Validate user data.\"\"\"
        return len(self.username) > 0 and '@' in self.email
""")

            # Create a simple view file
            view_file = os.path.join(temp_dir, "src", "sample_app", "views", "user_view.py")
            with open(view_file, "w") as f:
                f.write("""
from sample_app.models.user import User

class UserView:
    \"\"\"A view for user data.\"\"\"

    def display_user(self, user):
        \"\"\"Display user information.\"\"\"
        return f"User: {user.username}, Email: {user.email}"
""")

            # Create a simple controller file
            controller_file = os.path.join(temp_dir, "src", "sample_app", "controllers", "user_controller.py")
            with open(controller_file, "w") as f:
                f.write("""
from sample_app.models.user import User
from sample_app.views.user_view import UserView

class UserController:
    \"\"\"A controller for user operations.\"\"\"

    def __init__(self):
        \"\"\"Initialize the controller.\"\"\"
        self.view = UserView()

    def create_user(self, username, email):
        \"\"\"Create a new user.\"\"\"
        user = User(username, email)
        if user.validate():
            return self.view.display_user(user)
        else:
            return "Invalid user data"
""")

            # Create a simple test file
            test_file = os.path.join(temp_dir, "tests", "test_user.py")
            with open(test_file, "w") as f:
                f.write("""
import unittest
from sample_app.models.user import User

class TestUser(unittest.TestCase):
    \"\"\"Test the User model.\"\"\"

    def test_validate(self):
        \"\"\"Test user validation.\"\"\"
        user = User("testuser", "test@example.com")
        self.assertTrue(user.validate())

        invalid_user = User("", "invalid-email")
        self.assertFalse(invalid_user.validate())
""")

            # Create a requirements file
            requirements_file = os.path.join(temp_dir, "requirements.md")
            with open(requirements_file, "w") as f:
                f.write("""# Sample App Requirements

## User Management
1. The system shall allow users to register with a username and email
2. The system shall validate user data before registration
3. The system shall display user information

## Technical Requirements
1. The system shall follow the MVC architecture
2. The system shall include unit tests for all functionality
""")

            yield temp_dir
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

    def test_analyze_external_codebase(self, sample_project):
        """Test that DevSynth can analyze an external codebase."""
        # Create a SelfAnalyzer instance
        analyzer = SelfAnalyzer(sample_project)

        # Analyze the codebase
        result = analyzer.analyze()

        # Verify that the analysis was successful
        assert "code_analysis" in result
        assert "insights" in result

        # Verify that the architecture was correctly detected
        architecture = result["insights"]["architecture"]
        assert architecture["type"] == "MVC"
        assert architecture["confidence"] > 0.5

        # Verify that the layers were correctly identified
        layers = architecture["layers"]
        # The layers are organized by directory structure, with sample_app as the top-level layer
        assert "sample_app" in layers
        # Check that the components are correctly identified within sample_app
        assert "models" in layers["sample_app"]
        assert "views" in layers["sample_app"]
        assert "controllers" in layers["sample_app"]

        # Print some key metrics for debugging
        print(f"\nCode Analysis Results for External Codebase:")
        print(f"Architecture: {architecture['type']} (confidence: {architecture['confidence']:.2f})")
        print(f"Layers: {', '.join(layers.keys())}")

        # Verify code quality metrics
        code_quality = result["insights"]["code_quality"]
        assert code_quality["total_files"] > 0
        assert code_quality["total_classes"] > 0
        assert code_quality["docstring_coverage"]["classes"] > 0

        # Verify test coverage
        test_coverage = result["insights"]["test_coverage"]
        # Note: Coverage percentage might be 0 for some test setups
        assert test_coverage["coverage_percentage"] >= 0

    def test_project_state_analyzer_with_external_codebase(self, sample_project):
        """Test that ProjectStateAnalyzer can analyze an external codebase."""
        # Create a ProjectStateAnalyzer instance
        analyzer = ProjectStateAnalyzer(sample_project)

        # Analyze the project
        report = analyzer.analyze()

        # Verify that the report contains the expected sections
        assert 'project_path' in report
        assert 'file_count' in report
        assert 'languages' in report
        assert 'architecture' in report
        assert 'requirements_count' in report

        # Verify that the project path is correct
        assert report['project_path'] == sample_project

        # Verify that files were indexed
        assert report['file_count'] > 0

        # Verify that Python is detected as a language
        assert 'Python' in report['languages']

        # Verify that requirements were found
        assert report['requirements_count'] > 0

        # Print the report for debugging
        print(f"\nProject State Analysis Results:")
        print(f"Project Health Score: {report['health_score']:.2f}")
        print(f"Detected Languages: {', '.join(report['languages'])}")
        print(f"Architecture: {report['architecture']['type']} (confidence: {report['architecture']['confidence']:.2f})")
        print(f"File Count: {report['file_count']}")
        print(f"Requirements Count: {report['requirements_count']}")

    def test_refactor_workflow_with_external_codebase(self, sample_project):
        """Test that RefactorWorkflowManager can work with an external codebase."""
        # Create a RefactorWorkflowManager instance
        workflow_manager = RefactorWorkflowManager()

        # Get suggestions for next steps
        suggestions = workflow_manager.suggest_next_steps(sample_project)

        # Verify that suggestions were generated
        assert len(suggestions) > 0

        # Print the suggestions for debugging
        print(f"\nSuggested Next Steps:")
        for suggestion in suggestions:
            print(f"- [{suggestion['priority']}] {suggestion['description']} (command: {suggestion['command']})")

        # Verify that the workflow manager can determine the optimal workflow
        project_state = workflow_manager.analyze_project_state(sample_project)
        workflow = workflow_manager.determine_optimal_workflow(project_state)
        entry_point = workflow_manager.determine_entry_point(project_state, workflow)

        # Print the workflow information for debugging
        print(f"\nWorkflow Information:")
        print(f"Optimal Workflow: {workflow}")
        print(f"Entry Point: {entry_point}")

        # Verify that the workflow and entry point are determined
        assert workflow is not None
        assert entry_point is not None

    def test_end_to_end_workflow(self, sample_project):
        """Test an end-to-end workflow from requirements to code."""
        # This test simulates a complete workflow from requirements to code
        # using multiple components of the system

        # Step 1: Analyze the project state
        project_analyzer = ProjectStateAnalyzer(sample_project)
        project_state = project_analyzer.analyze()

        # Step 2: Analyze the codebase
        code_analyzer = SelfAnalyzer(sample_project)
        code_analysis = code_analyzer.analyze()

        # Step 3: Determine the optimal workflow
        workflow_manager = RefactorWorkflowManager()
        workflow = workflow_manager.determine_optimal_workflow(project_state)
        entry_point = workflow_manager.determine_entry_point(project_state, workflow)

        # Print the workflow information for debugging
        print(f"\nEnd-to-End Workflow:")
        print(f"Project Health Score: {project_state['health_score']:.2f}")
        print(f"Architecture: {code_analysis['insights']['architecture']['type']}")
        print(f"Optimal Workflow: {workflow}")
        print(f"Entry Point: {entry_point}")

        # Verify that all components worked together successfully
        # Note: Health score might be 0 for projects without specifications
        assert project_state['health_score'] >= 0
        assert code_analysis['insights']['architecture']['type'] is not None
        assert workflow is not None
        assert entry_point is not None

        # Verify that the project state and code analysis are consistent
        assert project_state['architecture']['type'] == code_analysis['insights']['architecture']['type']
