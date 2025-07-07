"""
Unit tests for the ProjectStateAnalyzer class.

This module contains tests for the ProjectStateAnalyzer class, which analyzes
the state of a project, including its architecture, components, and alignment
between requirements, specifications, and code.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from devsynth.application.code_analysis.project_state_analyzer import ProjectStateAnalyzer


@pytest.fixture
def test_project_dir():
    """Create a temporary directory with a test project structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a basic project structure
        project_dir = Path(temp_dir)
        
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
        
        yield str(project_dir)


class TestProjectStateAnalyzer:
    """Test the ProjectStateAnalyzer class."""
    
    def test_initialization(self, test_project_dir):
        """Test that the analyzer can be initialized with a project path."""
        analyzer = ProjectStateAnalyzer(test_project_dir)
        assert analyzer.project_path == test_project_dir
        assert analyzer.files == {}
        assert analyzer.languages == {}
        assert analyzer.architecture == {}
        
    def test_analyze(self, test_project_dir):
        """Test the analyze method."""
        analyzer = ProjectStateAnalyzer(test_project_dir)
        result = analyzer.analyze()
        
        # Check that the result contains the expected keys
        assert "files" in result
        assert "languages" in result
        assert "architecture" in result
        assert "components" in result
        assert "health_report" in result
        
    def test_index_files(self, test_project_dir):
        """Test the _index_files method."""
        analyzer = ProjectStateAnalyzer(test_project_dir)
        analyzer._index_files()
        
        # Check that files were indexed
        assert len(analyzer.files) > 0
        
        # Check that Python files were found
        python_files = [f for f in analyzer.files.values() if f.get("language") == "python"]
        assert len(python_files) >= 4  # 3 source files + 1 test file
        
    def test_detect_languages(self, test_project_dir):
        """Test the _detect_languages method."""
        analyzer = ProjectStateAnalyzer(test_project_dir)
        analyzer._index_files()
        analyzer._detect_languages()
        
        # Check that Python was detected
        assert "python" in analyzer.languages
        assert analyzer.languages["python"]["percentage"] > 0
        
    def test_infer_architecture(self, test_project_dir):
        """Test the _infer_architecture method."""
        analyzer = ProjectStateAnalyzer(test_project_dir)
        analyzer._index_files()
        analyzer._infer_architecture()
        
        # Check that MVC architecture was detected
        assert "mvc" in analyzer.architecture
        assert analyzer.architecture["mvc"]["confidence"] > 0
        
        # Check that hexagonal architecture was detected
        assert "hexagonal" in analyzer.architecture
        assert analyzer.architecture["hexagonal"]["confidence"] > 0
        
    def test_identify_components(self, test_project_dir):
        """Test the _identify_components method."""
        analyzer = ProjectStateAnalyzer(test_project_dir)
        analyzer._index_files()
        analyzer._infer_architecture()
        
        # Assume MVC has the highest confidence
        components = analyzer._identify_components("mvc")
        
        # Check that components were identified
        assert "models" in components
        assert "views" in components
        assert "controllers" in components
        
    def test_analyze_requirements_spec_alignment(self, test_project_dir):
        """Test the _analyze_requirements_spec_alignment method."""
        analyzer = ProjectStateAnalyzer(test_project_dir)
        analyzer._index_files()
        
        # Mock the extraction methods to return known values
        with patch.object(analyzer, '_extract_requirements') as mock_extract_req:
            with patch.object(analyzer, '_extract_specifications') as mock_extract_spec:
                mock_extract_req.return_value = [
                    {"id": "REQ-1", "text": "The system shall allow users to create accounts."}
                ]
                mock_extract_spec.return_value = [
                    {"id": "SPEC-1", "text": "User Creation: The system will provide an API endpoint for user creation."}
                ]
                
                alignment = analyzer._analyze_requirements_spec_alignment()
                
                # Check that alignment was analyzed
                assert "matched_requirements" in alignment
                assert "unmatched_requirements" in alignment
                assert "orphaned_specifications" in alignment
                
                # Check that our requirement was matched
                assert len(alignment["matched_requirements"]) == 1
                assert alignment["matched_requirements"][0]["requirement"]["id"] == "REQ-1"
                
    def test_generate_health_report(self, test_project_dir):
        """Test the _generate_health_report method."""
        analyzer = ProjectStateAnalyzer(test_project_dir)
        
        # Create sample alignment data
        req_spec_alignment = {
            "matched_requirements": [
                {"requirement": {"id": "REQ-1"}, "specification": {"id": "SPEC-1"}}
            ],
            "unmatched_requirements": [],
            "orphaned_specifications": []
        }
        
        spec_code_alignment = {
            "implemented_specifications": [
                {"specification": {"id": "SPEC-1"}}
            ],
            "unimplemented_specifications": []
        }
        
        report = analyzer._generate_health_report(req_spec_alignment, spec_code_alignment)
        
        # Check that the report contains the expected sections
        assert "requirements_coverage" in report
        assert "specifications_implementation" in report
        assert "overall_health" in report
        assert "issues" in report
        assert "recommendations" in report
        
        # Check that the health scores are between 0 and 1
        assert 0 <= report["requirements_coverage"] <= 1
        assert 0 <= report["specifications_implementation"] <= 1
        assert 0 <= report["overall_health"] <= 1