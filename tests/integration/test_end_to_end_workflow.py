"""
End-to-end integration tests for DevSynth workflows.

These tests verify that DevSynth can successfully execute complete workflows
from requirements to code, including project analysis at different stages.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path

from devsynth.application.cli.cli_commands import (
    init_cmd, analyze_cmd, spec_cmd, test_cmd, code_cmd
)
from devsynth.application.code_analysis.project_state_analyzer import ProjectStateAnalyzer

class TestEndToEndWorkflow:
    """Tests for end-to-end DevSynth workflows."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)
    
    def test_complete_workflow(self, temp_project_dir, monkeypatch):
        """
        Test a complete workflow from requirements to code.
        
        This test simulates a complete development workflow:
        1. Initialize a new project
        2. Create requirements
        3. Analyze the project state (should detect missing specifications and code)
        4. Generate specifications from requirements
        5. Analyze the project state again (should detect missing code)
        6. Generate tests from specifications
        7. Generate code from tests
        8. Analyze the final project state (should have good alignment)
        """
        # Set the current working directory to the temporary project directory
        original_dir = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            # Step 1: Initialize a new project
            init_cmd(path=temp_project_dir)
            
            # Verify that the project was initialized
            assert os.path.exists(os.path.join(temp_project_dir, '.devsynth'))
            
            # Step 2: Create requirements
            requirements_dir = os.path.join(temp_project_dir, 'docs')
            os.makedirs(requirements_dir, exist_ok=True)
            
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
            
            with open(os.path.join(requirements_dir, 'requirements.md'), 'w') as f:
                f.write(requirements_content)
            
            # Step 3: Analyze the project state (should detect missing specifications and code)
            analyzer = ProjectStateAnalyzer(temp_project_dir)
            initial_report = analyzer.analyze()
            
            # Verify that requirements were found
            assert initial_report['requirements_count'] > 0
            
            # Verify that no specifications were found
            assert initial_report['specifications_count'] == 0
            
            # Verify that no code files were found (except for the .devsynth directory)
            assert initial_report['code_count'] == 0
            
            # Verify that missing specifications issue is reported
            missing_specs_issue = next((issue for issue in initial_report['issues'] 
                                       if issue['type'] == 'missing_specifications'), None)
            assert missing_specs_issue is not None
            
            # Step 4: Generate specifications from requirements
            # Mock user input for the spec command
            monkeypatch.setattr('builtins.input', lambda _: 'y')  # Automatically answer 'yes' to prompts
            
            # Run the spec command
            spec_cmd(requirements_file=os.path.join(requirements_dir, 'requirements.md'))
            
            # Verify that specifications were generated
            assert os.path.exists(os.path.join(temp_project_dir, 'specs.md'))
            
            # Step 5: Analyze the project state again (should detect missing code)
            mid_report = analyzer.analyze()
            
            # Verify that requirements were found
            assert mid_report['requirements_count'] > 0
            
            # Verify that specifications were found
            assert mid_report['specifications_count'] > 0
            
            # Verify that no code files were found yet
            assert mid_report['code_count'] == 0
            
            # Verify that missing tests issue is reported
            missing_tests_issue = next((issue for issue in mid_report['issues'] 
                                      if issue['type'] == 'missing_tests'), None)
            assert missing_tests_issue is not None
            
            # Step 6: Generate tests from specifications
            test_cmd(spec_file=os.path.join(temp_project_dir, 'specs.md'))
            
            # Verify that tests were generated
            assert os.path.exists(os.path.join(temp_project_dir, 'tests'))
            
            # Step 7: Generate code from tests
            code_cmd()
            
            # Verify that code was generated
            assert os.path.exists(os.path.join(temp_project_dir, 'src'))
            
            # Step 8: Analyze the final project state
            final_report = analyzer.analyze()
            
            # Verify that requirements were found
            assert final_report['requirements_count'] > 0
            
            # Verify that specifications were found
            assert final_report['specifications_count'] > 0
            
            # Verify that tests were found
            assert final_report['test_count'] > 0
            
            # Verify that code files were found
            assert final_report['code_count'] > 0
            
            # Verify that the health score improved
            assert final_report['health_score'] > initial_report['health_score']
            
            # Print the final report for debugging
            print(f"Final Project Health Score: {final_report['health_score']:.2f}")
            print(f"Requirements Count: {final_report['requirements_count']}")
            print(f"Specifications Count: {final_report['specifications_count']}")
            print(f"Test Count: {final_report['test_count']}")
            print(f"Code Count: {final_report['code_count']}")
            
            # Print issues and recommendations
            print("\nFinal Issues:")
            for issue in final_report['issues']:
                print(f"- [{issue['severity']}] {issue['description']}")
            
            print("\nFinal Recommendations:")
            for recommendation in final_report['recommendations']:
                print(f"- {recommendation}")
            
        finally:
            # Restore the original working directory
            os.chdir(original_dir)
    
    def test_inconsistent_project_workflow(self, temp_project_dir):
        """
        Test workflow with an inconsistent project state.
        
        This test simulates a workflow with an inconsistent project state:
        1. Initialize a new project
        2. Create requirements
        3. Create code without specifications or tests
        4. Analyze the project state (should detect inconsistencies)
        5. Generate specifications from requirements
        6. Generate tests from specifications
        7. Analyze the final project state (should have improved alignment)
        """
        # Set the current working directory to the temporary project directory
        original_dir = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            # Step 1: Initialize a new project
            init_cmd(path=temp_project_dir)
            
            # Verify that the project was initialized
            assert os.path.exists(os.path.join(temp_project_dir, '.devsynth'))
            
            # Step 2: Create requirements
            requirements_dir = os.path.join(temp_project_dir, 'docs')
            os.makedirs(requirements_dir, exist_ok=True)
            
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
            
            with open(os.path.join(requirements_dir, 'requirements.md'), 'w') as f:
                f.write(requirements_content)
            
            # Step 3: Create code without specifications or tests
            src_dir = os.path.join(temp_project_dir, 'src')
            os.makedirs(src_dir, exist_ok=True)
            
            # Create a user.py file with authentication code
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
            
            with open(os.path.join(src_dir, 'user.py'), 'w') as f:
                f.write(user_code)
            
            # Step 4: Analyze the project state (should detect inconsistencies)
            analyzer = ProjectStateAnalyzer(temp_project_dir)
            initial_report = analyzer.analyze()
            
            # Verify that requirements were found
            assert initial_report['requirements_count'] > 0
            
            # Verify that no specifications were found
            assert initial_report['specifications_count'] == 0
            
            # Verify that code files were found
            assert initial_report['code_count'] > 0
            
            # Verify that missing specifications issue is reported
            missing_specs_issue = next((issue for issue in initial_report['issues'] 
                                       if issue['type'] == 'missing_specifications'), None)
            assert missing_specs_issue is not None
            
            # Verify that missing tests issue is reported
            missing_tests_issue = next((issue for issue in initial_report['issues'] 
                                      if issue['type'] == 'missing_tests'), None)
            assert missing_tests_issue is not None
            
            # Step 5: Generate specifications from requirements
            spec_cmd(requirements_file=os.path.join(requirements_dir, 'requirements.md'))
            
            # Verify that specifications were generated
            assert os.path.exists(os.path.join(temp_project_dir, 'specs.md'))
            
            # Step 6: Generate tests from specifications
            test_cmd(spec_file=os.path.join(temp_project_dir, 'specs.md'))
            
            # Verify that tests were generated
            assert os.path.exists(os.path.join(temp_project_dir, 'tests'))
            
            # Step 7: Analyze the final project state
            final_report = analyzer.analyze()
            
            # Verify that requirements were found
            assert final_report['requirements_count'] > 0
            
            # Verify that specifications were found
            assert final_report['specifications_count'] > 0
            
            # Verify that tests were found
            assert final_report['test_count'] > 0
            
            # Verify that code files were found
            assert final_report['code_count'] > 0
            
            # Verify that the health score improved
            assert final_report['health_score'] > initial_report['health_score']
            
            # Print the final report for debugging
            print(f"Final Project Health Score: {final_report['health_score']:.2f}")
            print(f"Requirements Count: {final_report['requirements_count']}")
            print(f"Specifications Count: {final_report['specifications_count']}")
            print(f"Test Count: {final_report['test_count']}")
            print(f"Code Count: {final_report['code_count']}")
            
        finally:
            # Restore the original working directory
            os.chdir(original_dir)

if __name__ == "__main__":
    pytest.main(["-v", "test_end_to_end_workflow.py"])