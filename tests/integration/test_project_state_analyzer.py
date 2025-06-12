"""
Integration tests for the ProjectStateAnalyzer class.

These tests verify that the ProjectStateAnalyzer can correctly analyze
a project's structure, languages, architecture, and consistency between
requirements, specifications, and code.
"""

import os
import pytest
from pathlib import Path

from devsynth.application.code_analysis.project_state_analyzer import ProjectStateAnalyzer

class TestProjectStateAnalyzer:
    """Tests for the ProjectStateAnalyzer class."""
    
    def test_analyze_devsynth_project(self):
        """Test analyzing the DevSynth project itself."""
        # Get the project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        # Create a ProjectStateAnalyzer for the DevSynth project
        analyzer = ProjectStateAnalyzer(project_root)
        
        # Analyze the project
        report = analyzer.analyze()
        
        # Verify that the report contains the expected sections
        assert 'project_path' in report
        assert 'file_count' in report
        assert 'languages' in report
        assert 'architecture' in report
        assert 'requirements_count' in report
        assert 'specifications_count' in report
        assert 'test_count' in report
        assert 'code_count' in report
        assert 'health_score' in report
        assert 'issues' in report
        assert 'recommendations' in report
        
        # Verify that the project path is correct
        assert report['project_path'] == project_root
        
        # Verify that files were indexed
        assert report['file_count'] > 0
        
        # Verify that Python is detected as a language
        assert 'Python' in report['languages']
        
        # Verify that tests were found
        assert report['test_count'] > 0
        
        # Verify that code files were found
        assert report['code_count'] > 0
        
        # Verify that the architecture was detected
        assert report['architecture'] is not None
        assert 'type' in report['architecture']
        assert 'confidence' in report['architecture']
        
        # DevSynth uses a hexagonal architecture, so this should be detected
        assert report['architecture']['type'] == 'Hexagonal'
        assert report['architecture']['confidence'] > 0.5
        
        # Print the report for debugging
        print(f"Project Health Score: {report['health_score']:.2f}")
        print(f"Detected Languages: {', '.join(report['languages'])}")
        print(f"Architecture: {report['architecture']['type']} (confidence: {report['architecture']['confidence']:.2f})")
        print(f"File Count: {report['file_count']}")
        print(f"Test Count: {report['test_count']}")
        print(f"Code Count: {report['code_count']}")
        
        # Print issues and recommendations
        print("\nIssues:")
        for issue in report['issues']:
            print(f"- [{issue['severity']}] {issue['description']}")
        
        print("\nRecommendations:")
        for recommendation in report['recommendations']:
            print(f"- {recommendation}")
    
    def test_analyze_with_missing_files(self, tmp_path):
        """Test analyzing a project with missing files."""
        # Create a temporary project directory
        project_dir = tmp_path / "empty_project"
        project_dir.mkdir()
        
        # Create a ProjectStateAnalyzer for the empty project
        analyzer = ProjectStateAnalyzer(str(project_dir))
        
        # Analyze the project
        report = analyzer.analyze()
        
        # Verify that the report contains the expected sections
        assert 'project_path' in report
        assert 'file_count' in report
        assert 'languages' in report
        assert 'architecture' in report
        assert 'requirements_count' in report
        assert 'specifications_count' in report
        assert 'test_count' in report
        assert 'code_count' in report
        assert 'health_score' in report
        assert 'issues' in report
        assert 'recommendations' in report
        
        # Verify that the project path is correct
        assert report['project_path'] == str(project_dir)
        
        # Verify that no files were indexed
        assert report['file_count'] == 0
        
        # Verify that no languages were detected
        assert len(report['languages']) == 0
        
        # Verify that no tests were found
        assert report['test_count'] == 0
        
        # Verify that no code files were found
        assert report['code_count'] == 0
        
        # Verify that the architecture was not detected
        assert report['architecture'] is not None
        assert report['architecture']['type'] == 'Unknown'
        
        # Verify that issues were identified
        assert len(report['issues']) > 0
        
        # Verify that recommendations were provided
        assert len(report['recommendations']) > 0
        
        # Verify that missing requirements issue is reported
        missing_requirements_issue = next((issue for issue in report['issues'] if issue['type'] == 'missing_requirements'), None)
        assert missing_requirements_issue is not None
        assert missing_requirements_issue['severity'] == 'high'
        
        # Verify that missing specifications issue is reported
        missing_specs_issue = next((issue for issue in report['issues'] if issue['type'] == 'missing_specifications'), None)
        assert missing_specs_issue is not None
        assert missing_specs_issue['severity'] == 'high'
        
        # Verify that missing tests issue is reported
        missing_tests_issue = next((issue for issue in report['issues'] if issue['type'] == 'missing_tests'), None)
        assert missing_tests_issue is not None
        assert missing_tests_issue['severity'] == 'medium'
    
    def test_analyze_with_requirements_and_code(self, tmp_path):
        """Test analyzing a project with requirements and code but no specifications."""
        # Create a temporary project directory
        project_dir = tmp_path / "partial_project"
        project_dir.mkdir()
        
        # Create a requirements file
        requirements_dir = project_dir / "docs"
        requirements_dir.mkdir()
        requirements_file = requirements_dir / "requirements.md"
        requirements_file.write_text("""
        # Project Requirements
        
        ## User Authentication
        1. The system shall provide user registration functionality
        2. The system shall support login with username and password
        3. The system shall implement password reset via email
        
        ## Data Management
        1. The system shall store user data securely
        2. The system shall provide CRUD operations for user profiles
        """)
        
        # Create a code file
        src_dir = project_dir / "src"
        src_dir.mkdir()
        code_file = src_dir / "user.py"
        code_file.write_text("""
        class User:
            def __init__(self, username, password):
                self.username = username
                self.password = password
                
            def register(self):
                # Implementation for user registration
                pass
                
            def login(self):
                # Implementation for user login
                pass
                
            def reset_password(self):
                # Implementation for password reset
                pass
        """)
        
        # Create a ProjectStateAnalyzer for the partial project
        analyzer = ProjectStateAnalyzer(str(project_dir))
        
        # Analyze the project
        report = analyzer.analyze()
        
        # Verify that the report contains the expected sections
        assert 'project_path' in report
        assert 'file_count' in report
        assert 'languages' in report
        assert 'architecture' in report
        assert 'requirements_count' in report
        assert 'specifications_count' in report
        assert 'test_count' in report
        assert 'code_count' in report
        assert 'health_score' in report
        assert 'issues' in report
        assert 'recommendations' in report
        
        # Verify that the project path is correct
        assert report['project_path'] == str(project_dir)
        
        # Verify that files were indexed
        assert report['file_count'] > 0
        
        # Verify that Python is detected as a language
        assert 'Python' in report['languages']
        
        # Verify that requirements were found
        assert report['requirements_count'] > 0
        
        # Verify that no specifications were found
        assert report['specifications_count'] == 0
        
        # Verify that no tests were found
        assert report['test_count'] == 0
        
        # Verify that code files were found
        assert report['code_count'] > 0
        
        # Verify that issues were identified
        assert len(report['issues']) > 0
        
        # Verify that recommendations were provided
        assert len(report['recommendations']) > 0
        
        # Verify that missing specifications issue is reported
        missing_specs_issue = next((issue for issue in report['issues'] if issue['type'] == 'missing_specifications'), None)
        assert missing_specs_issue is not None
        assert missing_specs_issue['severity'] == 'high'
        
        # Verify that missing tests issue is reported
        missing_tests_issue = next((issue for issue in report['issues'] if issue['type'] == 'missing_tests'), None)
        assert missing_tests_issue is not None
        assert missing_tests_issue['severity'] == 'medium'

if __name__ == "__main__":
    pytest.main(["-v", "test_project_state_analyzer.py"])
