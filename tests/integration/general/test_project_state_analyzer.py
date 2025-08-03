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
    """Tests for the ProjectStateAnalyzer class.

ReqID: N/A"""

    @pytest.mark.medium
    def test_analyze_devsynth_project_succeeds(self):
        """Test analyzing the DevSynth project itself.

ReqID: N/A"""
        project_root = os.path.abspath(os.path.join(os.path.dirname(
            __file__), '..', '..'))
        analyzer = ProjectStateAnalyzer(project_root)
        report = analyzer.analyze()
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
        assert report['project_path'] == project_root
        assert report['file_count'] > 0
        assert 'Python' in report['languages']
        assert report['test_count'] > 0
        assert report['code_count'] > 0
        assert report['architecture'] is not None
        assert 'type' in report['architecture']
        assert 'confidence' in report['architecture']
        assert report['architecture']['type'] == 'Hexagonal'
        assert report['architecture']['confidence'] > 0.5
        print(f"Project Health Score: {report['health_score']:.2f}")
        print(f"Detected Languages: {', '.join(report['languages'])}")
        print(
            f"Architecture: {report['architecture']['type']} (confidence: {report['architecture']['confidence']:.2f})"
            )
        print(f"File Count: {report['file_count']}")
        print(f"Test Count: {report['test_count']}")
        print(f"Code Count: {report['code_count']}")
        print('\nIssues:')
        for issue in report['issues']:
            print(f"- [{issue['severity']}] {issue['description']}")
        print('\nRecommendations:')
        for recommendation in report['recommendations']:
            print(f'- {recommendation}')

    @pytest.mark.medium
    def test_analyze_with_missing_files_succeeds(self, tmp_path):
        """Test analyzing a project with missing files.

ReqID: N/A"""
        project_dir = tmp_path / 'empty_project'
        project_dir.mkdir()
        analyzer = ProjectStateAnalyzer(str(project_dir))
        report = analyzer.analyze()
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
        assert report['project_path'] == str(project_dir)
        assert report['file_count'] == 0
        assert len(report['languages']) == 0
        assert report['test_count'] == 0
        assert report['code_count'] == 0
        assert report['architecture'] is not None
        assert report['architecture']['type'] == 'Unknown'
        assert len(report['issues']) > 0
        assert len(report['recommendations']) > 0
        missing_requirements_issue = next((issue for issue in report[
            'issues'] if issue['type'] == 'missing_requirements'), None)
        assert missing_requirements_issue is not None
        assert missing_requirements_issue['severity'] == 'high'
        missing_specs_issue = next((issue for issue in report['issues'] if 
            issue['type'] == 'missing_specifications'), None)
        assert missing_specs_issue is not None
        assert missing_specs_issue['severity'] == 'high'
        missing_tests_issue = next((issue for issue in report['issues'] if 
            issue['type'] == 'missing_tests'), None)
        assert missing_tests_issue is not None
        assert missing_tests_issue['severity'] == 'medium'

    @pytest.mark.medium
    def test_analyze_with_requirements_and_code_succeeds(self, tmp_path):
        """Test analyzing a project with requirements and code but no specifications.

ReqID: N/A"""
        project_dir = tmp_path / 'partial_project'
        project_dir.mkdir()
        requirements_dir = project_dir / 'docs'
        requirements_dir.mkdir()
        requirements_file = requirements_dir / 'requirements.md'
        requirements_file.write_text(
            """
        # Project Requirements
        
        ## User Authentication
        1. The system shall provide user registration functionality
        2. The system shall support login with username and password
        3. The system shall implement password reset via email
        
        ## Data Management
        1. The system shall store user data securely
        2. The system shall provide CRUD operations for user profiles
        """
            )
        src_dir = project_dir / 'src'
        src_dir.mkdir()
        code_file = src_dir / 'user.py'
        code_file.write_text(
            """
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
        """
            )
        analyzer = ProjectStateAnalyzer(str(project_dir))
        report = analyzer.analyze()
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
        assert report['project_path'] == str(project_dir)
        assert report['file_count'] > 0
        assert 'Python' in report['languages']
        assert report['requirements_count'] > 0
        assert report['specifications_count'] == 0
        assert report['test_count'] == 0
        assert report['code_count'] > 0
        assert len(report['issues']) > 0
        assert len(report['recommendations']) > 0
        missing_specs_issue = next((issue for issue in report['issues'] if 
            issue['type'] == 'missing_specifications'), None)
        assert missing_specs_issue is not None
        assert missing_specs_issue['severity'] == 'high'
        missing_tests_issue = next((issue for issue in report['issues'] if 
            issue['type'] == 'missing_tests'), None)
        assert missing_tests_issue is not None
        assert missing_tests_issue['severity'] == 'medium'


if __name__ == '__main__':
    pytest.main(['-v', 'test_project_state_analyzer.py'])
