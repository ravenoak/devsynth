"""
Integration tests for the RefactorWorkflowManager class.

These tests verify that the RefactorWorkflowManager can correctly analyze
a project's state, determine the optimal workflow, and suggest appropriate
next steps.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from devsynth.application.cli.cli_commands import init_cmd
from devsynth.application.orchestration.refactor_workflow import RefactorWorkflowManager


class TestRefactorWorkflowManager:
    """Tests for the RefactorWorkflowManager class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.medium
    def test_analyze_project_state_succeeds(self, temp_project_dir):
        """Test analyzing the project state.

        ReqID: N/A"""
        init_cmd(
            root=temp_project_dir,
            language="python",
            goals="",
            memory_backend="memory",
            auto_confirm=True,
        )
        requirements_dir = os.path.join(temp_project_dir, "docs")
        os.makedirs(requirements_dir, exist_ok=True)
        requirements_content = """
        # Project Requirements

        ## Feature 1
        1. Requirement 1
        2. Requirement 2

        ## Feature 2
        1. Requirement 3
        2. Requirement 4
        """
        with open(os.path.join(requirements_dir, "requirements.md"), "w") as f:
            f.write(requirements_content)
        manager = RefactorWorkflowManager()
        project_state = manager.analyze_project_state(temp_project_dir)
        assert "project_path" in project_state
        assert "file_count" in project_state
        assert "languages" in project_state
        assert "architecture" in project_state
        assert "requirements_count" in project_state
        assert "specifications_count" in project_state
        assert "test_count" in project_state
        assert "code_count" in project_state
        assert "health_score" in project_state
        assert "issues" in project_state
        assert "recommendations" in project_state
        assert project_state["requirements_count"] > 0
        assert project_state["specifications_count"] == 0
        assert project_state["test_count"] == 0
        assert project_state["code_count"] == 0

    @pytest.mark.medium
    def test_determine_optimal_workflow_succeeds(self, temp_project_dir):
        """Test determining the optimal workflow based on the project state.

        ReqID: N/A"""
        init_cmd(
            root=temp_project_dir,
            language="python",
            goals="",
            memory_backend="memory",
            auto_confirm=True,
        )
        requirements_dir = os.path.join(temp_project_dir, "docs")
        os.makedirs(requirements_dir, exist_ok=True)
        requirements_content = """
        # Project Requirements

        ## Feature 1
        1. Requirement 1
        2. Requirement 2

        ## Feature 2
        1. Requirement 3
        2. Requirement 4
        """
        with open(os.path.join(requirements_dir, "requirements.md"), "w") as f:
            f.write(requirements_content)
        manager = RefactorWorkflowManager()
        project_state = manager.analyze_project_state(temp_project_dir)
        workflow = manager.determine_optimal_workflow(project_state)
        assert workflow == "specifications"
        specifications_content = """
        # Project Specifications

        ## Feature 1
        1. Specification 1
        2. Specification 2

        ## Feature 2
        1. Specification 3
        2. Specification 4
        """
        with open(os.path.join(temp_project_dir, "specs.md"), "w") as f:
            f.write(specifications_content)
        project_state = manager.analyze_project_state(temp_project_dir)
        workflow = manager.determine_optimal_workflow(project_state)
        assert workflow == "tests"
        tests_dir = os.path.join(temp_project_dir, "tests")
        os.makedirs(tests_dir, exist_ok=True)
        test_content = """
        def test_feature_1():
            # Test implementation
            pass

        def test_feature_2():
            # Test implementation
            pass
        """
        with open(os.path.join(tests_dir, "test_features.py"), "w") as f:
            f.write(test_content)
        project_state = manager.analyze_project_state(temp_project_dir)
        workflow = manager.determine_optimal_workflow(project_state)
        assert workflow == "code"
        src_dir = os.path.join(temp_project_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        code_content = """
        class Feature1:
            def __init__(self):
                pass

            def method1(self):
                # Implementation
                pass

            def method2(self):
                # Implementation
                pass

        class Feature2:
            def __init__(self):
                pass

            def method1(self):
                # Implementation
                pass

            def method2(self):
                # Implementation
                pass
        """
        with open(os.path.join(src_dir, "features.py"), "w") as f:
            f.write(code_content)
        project_state = manager.analyze_project_state(temp_project_dir)
        workflow = manager.determine_optimal_workflow(project_state)
        assert workflow == "complete"

    @pytest.mark.medium
    def test_suggest_next_steps_succeeds(self, temp_project_dir):
        """Test suggesting next steps based on the project state.

        ReqID: N/A"""
        init_cmd(
            root=temp_project_dir,
            language="python",
            goals="",
            memory_backend="memory",
            auto_confirm=True,
        )
        manager = RefactorWorkflowManager()
        suggestions = manager.suggest_next_steps(temp_project_dir)
        assert len(suggestions) > 0
        assert suggestions[0]["command"] == "analyze"
        assert "requirements" in suggestions[0]["description"].lower()
        assert suggestions[0]["priority"] == "high"
        requirements_dir = os.path.join(temp_project_dir, "docs")
        os.makedirs(requirements_dir, exist_ok=True)
        requirements_content = """
        # Project Requirements

        ## Feature 1
        1. Requirement 1
        2. Requirement 2

        ## Feature 2
        1. Requirement 3
        2. Requirement 4
        """
        with open(os.path.join(requirements_dir, "requirements.md"), "w") as f:
            f.write(requirements_content)
        suggestions = manager.suggest_next_steps(temp_project_dir)
        assert len(suggestions) > 0
        assert suggestions[0]["command"] == "spec"
        assert "specifications" in suggestions[0]["description"].lower()
        assert suggestions[0]["priority"] == "high"

    @pytest.mark.medium
    def test_initialize_workflow_succeeds(self, temp_project_dir):
        """Test initializing a workflow based on the project state.

        ReqID: N/A"""
        init_cmd(
            root=temp_project_dir,
            language="python",
            goals="",
            memory_backend="memory",
            auto_confirm=True,
        )
        requirements_dir = os.path.join(temp_project_dir, "docs")
        os.makedirs(requirements_dir, exist_ok=True)
        requirements_content = """
        # Project Requirements

        ## Feature 1
        1. Requirement 1
        2. Requirement 2

        ## Feature 2
        1. Requirement 3
        2. Requirement 4
        """
        with open(os.path.join(requirements_dir, "requirements.md"), "w") as f:
            f.write(requirements_content)
        manager = RefactorWorkflowManager()
        workflow, entry_point, suggestions = manager.initialize_workflow(
            temp_project_dir
        )
        assert workflow == "specifications"
        assert entry_point == "spec"
        assert len(suggestions) > 0
        assert suggestions[0]["command"] == "spec"
        assert "specifications" in suggestions[0]["description"].lower()
        assert suggestions[0]["priority"] == "high"

    @pytest.mark.medium
    def test_execute_refactor_workflow_succeeds(self, temp_project_dir, monkeypatch):
        """Test executing a refactor workflow.

        ReqID: N/A"""
        init_cmd(
            root=temp_project_dir,
            language="python",
            goals="",
            memory_backend="memory",
            auto_confirm=True,
        )
        requirements_dir = os.path.join(temp_project_dir, "docs")
        os.makedirs(requirements_dir, exist_ok=True)
        requirements_content = """
        # Project Requirements

        ## Feature 1
        1. Requirement 1
        2. Requirement 2

        ## Feature 2
        1. Requirement 3
        2. Requirement 4
        """
        with open(os.path.join(requirements_dir, "requirements.md"), "w") as f:
            f.write(requirements_content)
        manager = RefactorWorkflowManager()

        def mock_execute_command(command, args):
            return {
                "success": True,
                "message": f"Executed {command} command",
                "result": {},
            }

        monkeypatch.setattr(manager, "execute_command", mock_execute_command)
        result = manager.execute_refactor_workflow(temp_project_dir)
        assert "success" in result
        assert "message" in result
        assert "workflow" in result
        assert "entry_point" in result
        assert "suggestions" in result
        assert result["workflow"] == "specifications"
        assert result["entry_point"] == "spec"
        assert len(result["suggestions"]) > 0


if __name__ == "__main__":
    pytest.main(["-v", "test_refactor_workflow.py"])
