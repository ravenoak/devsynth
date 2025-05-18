"""
Integration tests for the AdaptiveWorkflowManager class.

These tests verify that the AdaptiveWorkflowManager can correctly analyze
a project's state, determine the optimal workflow, and suggest appropriate
next steps.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path

from devsynth.application.orchestration.adaptive_workflow import AdaptiveWorkflowManager
from devsynth.application.cli.cli_commands import init_cmd

class TestAdaptiveWorkflowManager:
    """Tests for the AdaptiveWorkflowManager class."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)
    
    def test_analyze_project_state(self, temp_project_dir):
        """Test analyzing the project state."""
        # Initialize a new project
        init_cmd(path=temp_project_dir)
        
        # Create a requirements file
        requirements_dir = os.path.join(temp_project_dir, 'docs')
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
        
        with open(os.path.join(requirements_dir, 'requirements.md'), 'w') as f:
            f.write(requirements_content)
        
        # Create an AdaptiveWorkflowManager
        manager = AdaptiveWorkflowManager()
        
        # Analyze the project state
        project_state = manager.analyze_project_state(temp_project_dir)
        
        # Verify that the project state contains the expected sections
        assert 'project_path' in project_state
        assert 'file_count' in project_state
        assert 'languages' in project_state
        assert 'architecture' in project_state
        assert 'requirements_count' in project_state
        assert 'specifications_count' in project_state
        assert 'test_count' in project_state
        assert 'code_count' in project_state
        assert 'health_score' in project_state
        assert 'issues' in project_state
        assert 'recommendations' in project_state
        
        # Verify that requirements were found
        assert project_state['requirements_count'] > 0
        
        # Verify that no specifications were found
        assert project_state['specifications_count'] == 0
        
        # Verify that no tests were found
        assert project_state['test_count'] == 0
        
        # Verify that no code files were found
        assert project_state['code_count'] == 0
    
    def test_determine_optimal_workflow(self, temp_project_dir):
        """Test determining the optimal workflow based on the project state."""
        # Initialize a new project
        init_cmd(path=temp_project_dir)
        
        # Create a requirements file
        requirements_dir = os.path.join(temp_project_dir, 'docs')
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
        
        with open(os.path.join(requirements_dir, 'requirements.md'), 'w') as f:
            f.write(requirements_content)
        
        # Create an AdaptiveWorkflowManager
        manager = AdaptiveWorkflowManager()
        
        # Analyze the project state
        project_state = manager.analyze_project_state(temp_project_dir)
        
        # Determine the optimal workflow
        workflow = manager.determine_optimal_workflow(project_state)
        
        # Verify that the optimal workflow is "specifications" since we have requirements but no specifications
        assert workflow == "specifications"
        
        # Create a specifications file
        specifications_content = """
        # Project Specifications
        
        ## Feature 1
        1. Specification 1
        2. Specification 2
        
        ## Feature 2
        1. Specification 3
        2. Specification 4
        """
        
        with open(os.path.join(temp_project_dir, 'specs.md'), 'w') as f:
            f.write(specifications_content)
        
        # Analyze the project state again
        project_state = manager.analyze_project_state(temp_project_dir)
        
        # Determine the optimal workflow
        workflow = manager.determine_optimal_workflow(project_state)
        
        # Verify that the optimal workflow is "tests" since we have specifications but no tests
        assert workflow == "tests"
        
        # Create a test file
        tests_dir = os.path.join(temp_project_dir, 'tests')
        os.makedirs(tests_dir, exist_ok=True)
        
        test_content = """
        def test_feature_1():
            # Test implementation
            pass
        
        def test_feature_2():
            # Test implementation
            pass
        """
        
        with open(os.path.join(tests_dir, 'test_features.py'), 'w') as f:
            f.write(test_content)
        
        # Analyze the project state again
        project_state = manager.analyze_project_state(temp_project_dir)
        
        # Determine the optimal workflow
        workflow = manager.determine_optimal_workflow(project_state)
        
        # Verify that the optimal workflow is "code" since we have tests but no code
        assert workflow == "code"
        
        # Create a code file
        src_dir = os.path.join(temp_project_dir, 'src')
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
        
        with open(os.path.join(src_dir, 'features.py'), 'w') as f:
            f.write(code_content)
        
        # Analyze the project state again
        project_state = manager.analyze_project_state(temp_project_dir)
        
        # Determine the optimal workflow
        workflow = manager.determine_optimal_workflow(project_state)
        
        # Verify that the optimal workflow is "complete" since we have all artifacts
        assert workflow == "complete"
    
    def test_suggest_next_steps(self, temp_project_dir):
        """Test suggesting next steps based on the project state."""
        # Initialize a new project
        init_cmd(path=temp_project_dir)
        
        # Create an AdaptiveWorkflowManager
        manager = AdaptiveWorkflowManager()
        
        # Suggest next steps
        suggestions = manager.suggest_next_steps(temp_project_dir)
        
        # Verify that suggestions were provided
        assert len(suggestions) > 0
        
        # Verify that the first suggestion is to create requirements
        assert suggestions[0]['command'] == 'analyze'
        assert 'requirements' in suggestions[0]['description'].lower()
        assert suggestions[0]['priority'] == 'high'
        
        # Create a requirements file
        requirements_dir = os.path.join(temp_project_dir, 'docs')
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
        
        with open(os.path.join(requirements_dir, 'requirements.md'), 'w') as f:
            f.write(requirements_content)
        
        # Suggest next steps again
        suggestions = manager.suggest_next_steps(temp_project_dir)
        
        # Verify that suggestions were provided
        assert len(suggestions) > 0
        
        # Verify that the first suggestion is to generate specifications
        assert suggestions[0]['command'] == 'spec'
        assert 'specifications' in suggestions[0]['description'].lower()
        assert suggestions[0]['priority'] == 'high'
    
    def test_initialize_workflow(self, temp_project_dir):
        """Test initializing a workflow based on the project state."""
        # Initialize a new project
        init_cmd(path=temp_project_dir)
        
        # Create a requirements file
        requirements_dir = os.path.join(temp_project_dir, 'docs')
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
        
        with open(os.path.join(requirements_dir, 'requirements.md'), 'w') as f:
            f.write(requirements_content)
        
        # Create an AdaptiveWorkflowManager
        manager = AdaptiveWorkflowManager()
        
        # Initialize the workflow
        workflow, entry_point, suggestions = manager.initialize_workflow(temp_project_dir)
        
        # Verify that the workflow is "specifications"
        assert workflow == "specifications"
        
        # Verify that the entry point is "spec"
        assert entry_point == "spec"
        
        # Verify that suggestions were provided
        assert len(suggestions) > 0
        
        # Verify that the first suggestion is to generate specifications
        assert suggestions[0]['command'] == 'spec'
        assert 'specifications' in suggestions[0]['description'].lower()
        assert suggestions[0]['priority'] == 'high'
    
    def test_execute_adaptive_workflow(self, temp_project_dir, monkeypatch):
        """Test executing an adaptive workflow."""
        # Initialize a new project
        init_cmd(path=temp_project_dir)
        
        # Create a requirements file
        requirements_dir = os.path.join(temp_project_dir, 'docs')
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
        
        with open(os.path.join(requirements_dir, 'requirements.md'), 'w') as f:
            f.write(requirements_content)
        
        # Create an AdaptiveWorkflowManager
        manager = AdaptiveWorkflowManager()
        
        # Mock the execute_command method to avoid actually executing commands
        def mock_execute_command(command, args):
            return {
                'success': True,
                'message': f"Executed {command} command",
                'result': {}
            }
        
        monkeypatch.setattr(manager, 'execute_command', mock_execute_command)
        
        # Execute the adaptive workflow
        result = manager.execute_adaptive_workflow(temp_project_dir)
        
        # Verify that the result contains the expected fields
        assert 'success' in result
        assert 'message' in result
        assert 'workflow' in result
        assert 'entry_point' in result
        assert 'suggestions' in result
        
        # Verify that the workflow is "specifications"
        assert result['workflow'] == "specifications"
        
        # Verify that the entry point is "spec"
        assert result['entry_point'] == "spec"
        
        # Verify that suggestions were provided
        assert len(result['suggestions']) > 0

if __name__ == "__main__":
    pytest.main(["-v", "test_adaptive_workflow.py"])