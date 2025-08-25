"""
End-to-end integration tests for DevSynth workflows.

These tests verify that DevSynth can successfully execute complete workflows
from requirements to code, including project analysis at different stages.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from devsynth.application.cli.cli_commands import (
    code_cmd,
    init_cmd,
    inspect_cmd,
    spec_cmd,
    test_cmd,
)
from devsynth.application.code_analysis.project_state_analyzer import (
    ProjectStateAnalyzer,
)


class TestEndToEndWorkflow:
    """Tests for end-to-end DevSynth workflows.

    ReqID: N/A"""

    @pytest.fixture
    def temp_project_dir(self, tmpdir):
        """Create a temporary project directory for testing using pytest's tmpdir fixture."""
        # Convert tmpdir to string path
        temp_dir = str(tmpdir)
        yield temp_dir
        # No need for cleanup as pytest handles it automatically

    def test_complete_workflow_succeeds(self, temp_project_dir, tmpdir, monkeypatch):
        """Test a complete workflow from requirements to code.

        This test simulates a complete development workflow:
        1. Initialize a new project
        2. Create requirements
        3. Analyze the project state (should detect missing specifications and code)
        4. Generate specifications from requirements
        5. Analyze the project state again (should detect missing code)
        6. Generate tests from specifications
        7. Generate code from tests
        8. Analyze the final project state (should have good alignment)

        ReqID: N/A"""
        original_dir = os.getcwd()
        os.chdir(temp_project_dir)
        try:
            init_cmd(
                root=temp_project_dir,
                language="python",
                goals="",
                memory_backend="memory",
                auto_confirm=True,
            )
            assert os.path.exists(os.path.join(temp_project_dir, ".devsynth"))
            # Create docs directory in tmpdir
            requirements_dir = tmpdir.join("docs")
            requirements_dir.ensure(dir=True)
            requirements_content = """
            # Task Manager API Requirements
            
            ## User Management
            1. The system shall allow users to register with a username and password
            2. The system shall allow users to log in with their credentials
            3. The system shall allow users to log out
            4. The system shall allow users to update their profile information
            
            ## Task Management
            1. The system shall allow users to create new tasks with a title and description
            2. The system shall allow users to view their tasks
            3. The system shall allow users to update their tasks
            4. The system shall allow users to delete their tasks
            5. The system shall allow users to mark tasks as completed
            
            ## API Requirements
            1. The API shall use REST principles
            2. The API shall return responses in JSON format
            3. The API shall use proper HTTP status codes
            4. The API shall require authentication for protected endpoints
            """
            # Use tmpdir directly for file operations
            requirements_file = requirements_dir.join("requirements.md")
            requirements_file.write(requirements_content)
            analyzer = ProjectStateAnalyzer(temp_project_dir)
            initial_report = analyzer.analyze()
            assert initial_report["requirements_count"] > 0
            assert initial_report["specifications_count"] == 0
            assert initial_report["code_count"] == 0
            missing_specs_issue = next(
                (
                    issue
                    for issue in initial_report["issues"]
                    if issue["type"] == "missing_specifications"
                ),
                None,
            )
            assert missing_specs_issue is not None
            monkeypatch.setattr("builtins.input", lambda _: "y")
            spec_cmd(
                requirements_file=os.path.join(requirements_dir, "requirements.md")
            )
            assert os.path.exists(os.path.join(temp_project_dir, "specs.md"))
            mid_report = analyzer.analyze()
            assert mid_report["requirements_count"] > 0
            assert mid_report["specifications_count"] > 0
            assert mid_report["code_count"] == 0
            missing_tests_issue = next(
                (
                    issue
                    for issue in mid_report["issues"]
                    if issue["type"] == "missing_tests"
                ),
                None,
            )
            assert missing_tests_issue is not None
            test_cmd(spec_file=os.path.join(temp_project_dir, "specs.md"))
            assert os.path.exists(os.path.join(temp_project_dir, "tests"))
            code_cmd()
            assert os.path.exists(os.path.join(temp_project_dir, "src"))
            final_report = analyzer.analyze()
            assert final_report["requirements_count"] > 0
            assert final_report["specifications_count"] > 0
            assert final_report["test_count"] > 0
            assert final_report["code_count"] > 0
            assert final_report["health_score"] > initial_report["health_score"]
            print(f"Final Project Health Score: {final_report['health_score']:.2f}")
            print(f"Requirements Count: {final_report['requirements_count']}")
            print(f"Specifications Count: {final_report['specifications_count']}")
            print(f"Test Count: {final_report['test_count']}")
            print(f"Code Count: {final_report['code_count']}")
            print("\nFinal Issues:")
            for issue in final_report["issues"]:
                print(f"- [{issue['severity']}] {issue['description']}")
            print("\nFinal Recommendations:")
            for recommendation in final_report["recommendations"]:
                print(f"- {recommendation}")
        finally:
            os.chdir(original_dir)

    def test_inconsistent_project_workflow_succeeds(self, temp_project_dir, tmpdir):
        """Test workflow with an inconsistent project state.

        This test simulates a workflow with an inconsistent project state:
        1. Initialize a new project
        2. Create requirements
        3. Create code without specifications or tests
        4. Analyze the project state (should detect inconsistencies)
        5. Generate specifications from requirements
        6. Generate tests from specifications
        7. Analyze the final project state (should have improved alignment)

        ReqID: N/A"""
        original_dir = os.getcwd()
        os.chdir(temp_project_dir)
        try:
            init_cmd(
                root=temp_project_dir,
                language="python",
                goals="",
                memory_backend="memory",
                auto_confirm=True,
            )
            assert os.path.exists(os.path.join(temp_project_dir, ".devsynth"))
            # Create docs directory in tmpdir
            requirements_dir = tmpdir.join("docs")
            requirements_dir.ensure(dir=True)
            requirements_content = """
            # User Authentication Requirements
            
            ## Registration
            1. The system shall allow users to register with email and password
            2. The system shall validate email format
            3. The system shall enforce password complexity rules
            
            ## Authentication
            1. The system shall allow users to log in with email and password
            2. The system shall provide token-based authentication
            3. The system shall allow users to log out
            
            ## Password Management
            1. The system shall allow users to reset their password
            2. The system shall allow users to change their password
            """
            # Use tmpdir directly for file operations
            requirements_file = requirements_dir.join("requirements.md")
            requirements_file.write(requirements_content)

            # Create src directory in tmpdir
            src_dir = tmpdir.join("src")
            src_dir.ensure(dir=True)
            user_code = """
            class User:
                def __init__(self, email, password):
                    self.email = email
                    self.password = password
                    self.is_authenticated = False
                
                def register(self):
                    # Implementation for user registration
                    pass
                
                def login(self):
                    # Implementation for user login
                    self.is_authenticated = True
                    return True
                
                def logout(self):
                    # Implementation for user logout
                    self.is_authenticated = False
                    return True
                
                def reset_password(self, new_password):
                    # Implementation for password reset
                    self.password = new_password
                    return True
            """
            # Use tmpdir directly for file operations
            user_file = src_dir.join("user.py")
            user_file.write(user_code)
            analyzer = ProjectStateAnalyzer(temp_project_dir)
            initial_report = analyzer.analyze()
            assert initial_report["requirements_count"] > 0
            assert initial_report["specifications_count"] == 0
            assert initial_report["code_count"] > 0
            missing_specs_issue = next(
                (
                    issue
                    for issue in initial_report["issues"]
                    if issue["type"] == "missing_specifications"
                ),
                None,
            )
            assert missing_specs_issue is not None
            missing_tests_issue = next(
                (
                    issue
                    for issue in initial_report["issues"]
                    if issue["type"] == "missing_tests"
                ),
                None,
            )
            assert missing_tests_issue is not None
            spec_cmd(
                requirements_file=os.path.join(requirements_dir, "requirements.md")
            )
            assert os.path.exists(os.path.join(temp_project_dir, "specs.md"))
            test_cmd(spec_file=os.path.join(temp_project_dir, "specs.md"))
            assert os.path.exists(os.path.join(temp_project_dir, "tests"))
            final_report = analyzer.analyze()
            assert final_report["requirements_count"] > 0
            assert final_report["specifications_count"] > 0
            assert final_report["test_count"] > 0
            assert final_report["code_count"] > 0
            assert final_report["health_score"] > initial_report["health_score"]
            print(f"Final Project Health Score: {final_report['health_score']:.2f}")
            print(f"Requirements Count: {final_report['requirements_count']}")
            print(f"Specifications Count: {final_report['specifications_count']}")
            print(f"Test Count: {final_report['test_count']}")
            print(f"Code Count: {final_report['code_count']}")
        finally:
            os.chdir(original_dir)


if __name__ == "__main__":
    pytest.main(["-v", "test_end_to_end_workflow.py"])
