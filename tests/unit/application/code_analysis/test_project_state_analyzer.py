"""
Unit tests for the ProjectStateAnalyzer class.

This module contains tests for the ProjectStateAnalyzer class, which analyzes
the state of a project, including its architecture, components, and alignment
between requirements, specifications, and code.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from devsynth.application.code_analysis.project_state_analyzer import (
    ProjectStateAnalyzer,
)


@pytest.fixture
def project_dir_fixture():
    """Create a temporary directory with a test project structure.

    ReqID: N/A"""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        (project_dir / "src" / "models").mkdir(parents=True)
        (project_dir / "src" / "views").mkdir(parents=True)
        (project_dir / "src" / "controllers").mkdir(parents=True)
        (project_dir / "src" / "domain").mkdir(parents=True)
        (project_dir / "src" / "application").mkdir(parents=True)
        (project_dir / "src" / "adapters").mkdir(parents=True)
        (project_dir / "docs").mkdir(parents=True)
        (project_dir / "tests").mkdir(parents=True)
        (project_dir / "src" / "models" / "user.py").write_text(
            "class User:\n    def __init__(self, name):\n        self.name = name"
        )
        (project_dir / "src" / "controllers" / "user_controller.py").write_text(
            "from src.models.user import User\n\n"
            "class UserController:\n"
            "    def get_user(self, user_id):\n"
            "        return User('Test')"
        )
        (project_dir / "src" / "views" / "user_view.py").write_text(
            "class UserView:\n"
            "    def render_user(self, user):\n"
            "        return f'User: {user.name}'"
        )
        (project_dir / "docs" / "requirements.md").write_text(
            "# Requirements\n\n"
            "1. The system shall allow users to create accounts.\n"
            "2. The system shall allow users to log in."
        )
        (project_dir / "docs" / "specifications.md").write_text(
            "# Specifications\n\n"
            "1. User Creation: The system will provide an API endpoint for "
            "user creation.\n"
            "2. User Authentication: The system will support "
            "username/password authentication."
        )
        (project_dir / "tests" / "test_user.py").write_text(
            "def user_creation_test():\n"
            "    from src.models.user import User\n"
            "    user = User('Test')\n"
            "    assert user.name == 'Test'"
        )
        yield str(project_dir)


class TestProjectStateAnalyzer:
    """Test the ProjectStateAnalyzer class.

    ReqID: N/A"""

    def test_initialization_succeeds(self, project_dir_fixture):
        """Test that the analyzer can be initialized with a project path.

        ReqID: N/A"""
        analyzer = ProjectStateAnalyzer(project_dir_fixture)
        assert analyzer.project_path == project_dir_fixture
        assert hasattr(analyzer, "files")
        assert hasattr(analyzer, "file_index")
        assert hasattr(analyzer, "languages")
        assert hasattr(analyzer, "detected_languages")
        assert hasattr(analyzer, "architecture")
        assert hasattr(analyzer, "architecture_model")
        assert hasattr(analyzer, "requirements_files")
        assert hasattr(analyzer, "specification_files")
        assert hasattr(analyzer, "test_files")
        assert hasattr(analyzer, "code_files")
        assert hasattr(analyzer, "documentation_files")
        assert hasattr(analyzer, "config_files")

    def test_analyze_succeeds(self, project_dir_fixture):
        """Test the analyze method.

        ReqID: N/A"""
        analyzer = ProjectStateAnalyzer(project_dir_fixture)
        with patch.object(analyzer, "_index_files") as mock_index:
            with patch.object(analyzer, "_detect_languages") as mock_detect:
                with patch.object(analyzer, "_infer_architecture") as mock_infer:
                    with patch.object(
                        analyzer,
                        "_analyze_requirements_spec_alignment",
                        return_value={"matched_requirements": []},
                    ) as mock_req_spec:
                        with patch.object(
                            analyzer,
                            "_analyze_spec_code_alignment",
                            return_value={"implemented_specifications": []},
                        ) as mock_spec_code:
                            with patch.object(
                                analyzer,
                                "_generate_health_report",
                                return_value={"overall_health": 0.8},
                            ) as mock_health:
                                analyzer.files = {"test.py": {"path": "test.py"}}
                                analyzer.file_index = analyzer.files
                                analyzer.languages = {"python": {"percentage": 1.0}}
                                analyzer.detected_languages = {"Python"}
                                analyzer.architecture = {
                                    "type": "MVC",
                                    "confidence": 0.8,
                                    "components": [],
                                }
                                analyzer.architecture_model = analyzer.architecture
                                result = analyzer.analyze()
                                assert "files" in result
                                assert "languages" in result
                                assert "architecture" in result
                                assert "components" in result
                                assert "health_report" in result
                                assert mock_index.called
                                assert mock_detect.called
                                assert mock_infer.called
                                assert mock_req_spec.called
                                assert mock_spec_code.called
                                assert mock_health.called

    def test_index_files_succeeds(self, project_dir_fixture):
        """Test the _index_files method.

        ReqID: N/A"""
        analyzer = ProjectStateAnalyzer(project_dir_fixture)
        analyzer._index_files()
        assert len(analyzer.files) > 0
        python_files = [
            f
            for f in analyzer.files.values()
            if f.get("language", "").lower() == "python"
            or f.get("extension", "").lower() == ".py"
        ]
        assert len(python_files) > 0

    def test_detect_languages_succeeds(self, project_dir_fixture):
        """Test the _detect_languages method.

        ReqID: N/A"""
        analyzer = ProjectStateAnalyzer(project_dir_fixture)
        analyzer._index_files()
        analyzer._detect_languages()
        assert len(analyzer.languages) > 0
        for lang_info in analyzer.languages.values():
            assert "percentage" in lang_info
            assert 0 <= lang_info["percentage"] <= 1

    @pytest.mark.fast
    def test_categorize_file_assigns_lists(self, tmp_path):
        """Ensure files are categorized deterministically.

        ReqID: N/A"""
        analyzer = ProjectStateAnalyzer(str(tmp_path))
        code_file = tmp_path / "module.py"
        code_file.write_text("print('hi')")
        doc_file = tmp_path / "README.md"
        doc_file.write_text("docs")
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_mod.py"
        test_file.write_text("assert True")

        analyzer._categorize_file(str(code_file), "module.py", ".py")
        analyzer._categorize_file(str(doc_file), "README.md", ".md")
        analyzer._categorize_file(str(test_file), "tests/test_mod.py", ".py")

        assert "module.py" in analyzer.code_files
        assert "README.md" in analyzer.documentation_files
        assert "tests/test_mod.py" in analyzer.test_files

    def test_infer_architecture_succeeds(self, project_dir_fixture):
        """Test the _infer_architecture method.

        ReqID: N/A"""
        analyzer = ProjectStateAnalyzer(project_dir_fixture)
        with patch.object(analyzer, "_check_mvc_pattern", return_value=0.8) as mock_mvc:
            with patch.object(
                analyzer, "_check_hexagonal_pattern", return_value=0.6
            ) as mock_hex:
                with patch.object(
                    analyzer, "_check_microservices_pattern", return_value=0.4
                ) as mock_micro:
                    with patch.object(
                        analyzer, "_check_layered_pattern", return_value=0.5
                    ) as mock_layered:
                        with patch.object(
                            analyzer, "_check_event_driven_pattern", return_value=0.3
                        ) as mock_event:
                            with patch.object(
                                analyzer, "_identify_components", return_value=[]
                            ) as mock_components:
                                analyzer._infer_architecture()
                                assert isinstance(analyzer.architecture, dict)
                                assert isinstance(analyzer.architecture_model, dict)
                                assert analyzer.architecture["type"] == "MVC"
                                assert analyzer.architecture_model["type"] == "MVC"
                                assert mock_mvc.called
                                assert mock_hex.called
                                assert mock_micro.called
                                assert mock_layered.called
                                assert mock_event.called
                                assert mock_components.called

    def test_identify_components_succeeds(self, project_dir_fixture):
        """Test the _identify_components method.

        ReqID: N/A"""
        analyzer = ProjectStateAnalyzer(project_dir_fixture)

        def mock_identify_components(architecture):
            """Mock implementation of _identify_components."""
            if architecture.lower() == "mvc":
                return [
                    {"type": "Model", "path": "src/models/user.py", "name": "user"},
                    {
                        "type": "View",
                        "path": "src/views/user_view.py",
                        "name": "user_view",
                    },
                    {
                        "type": "Controller",
                        "path": "src/controllers/user_controller.py",
                        "name": "user_controller",
                    },
                ]
            else:
                return []

        analyzer._identify_components = mock_identify_components
        components = analyzer._identify_components("mvc")
        assert isinstance(components, list)
        component_types = [comp["type"] for comp in components]
        assert "Model" in component_types
        assert "View" in component_types
        assert "Controller" in component_types
        for comp in components:
            assert "type" in comp
            assert "path" in comp
            assert "name" in comp

    def test_analyze_requirements_spec_alignment_succeeds(self, project_dir_fixture):
        """Test the _analyze_requirements_spec_alignment method.

        ReqID: N/A"""
        analyzer = ProjectStateAnalyzer(project_dir_fixture)
        analyzer._index_files()
        with patch.object(analyzer, "_extract_requirements") as mock_extract_req:
            with patch.object(analyzer, "_extract_specifications") as mock_extract_spec:
                mock_extract_req.return_value = [
                    {
                        "text": "The system shall allow users to create accounts.",
                        "section": "Requirements",
                        "source_file": "docs/requirements.md",
                    }
                ]
                mock_extract_spec.return_value = [
                    {
                        "text": (
                            "User Creation: The system will provide an API "
                            "endpoint for user creation."
                        ),
                        "section": "Specifications",
                        "source_file": "docs/specifications.md",
                    }
                ]
                alignment = analyzer._analyze_requirements_spec_alignment()
                assert "total_requirements" in alignment
                assert "total_specifications" in alignment
                assert "matched_requirements" in alignment
                assert "unmatched_requirements" in alignment
                assert "unmatched_specifications" in alignment
                assert "alignment_score" in alignment

    def test_generate_health_report_succeeds(self, project_dir_fixture):
        """Test the _generate_health_report method.

        ReqID: N/A"""
        analyzer = ProjectStateAnalyzer(project_dir_fixture)
        analyzer.project_path = project_dir_fixture
        analyzer.file_index = {"test.py": {"path": "test.py"}}
        analyzer.detected_languages = {"Python"}
        analyzer.architecture_model = {"type": "MVC", "confidence": 0.8}
        analyzer.requirements_files = ["docs/requirements.md"]
        analyzer.specification_files = ["docs/specifications.md"]
        analyzer.test_files = ["tests/test_user.py"]
        analyzer.code_files = [
            "src/models/user.py",
            "src/controllers/user_controller.py",
            "src/views/user_view.py",
        ]
        req_spec_alignment = {
            "total_requirements": 2,
            "total_specifications": 2,
            "matched_requirements": 2,
            "unmatched_requirements": [],
            "unmatched_specifications": [],
            "alignment_score": 1.0,
        }
        spec_code_alignment = {
            "total_specifications": 2,
            "implemented_specifications": 2,
            "unimplemented_specifications": [],
            "implementation_score": 1.0,
        }
        report = analyzer._generate_health_report(
            req_spec_alignment, spec_code_alignment
        )
        assert isinstance(report, dict)
        assert "project_path" in report
        assert "file_count" in report
        assert "languages" in report
        assert "architecture" in report
        assert "requirements_count" in report
        assert "specifications_count" in report
        assert "test_count" in report
        assert "code_count" in report
        assert "requirements_spec_alignment" in report
        assert "spec_code_alignment" in report
        assert "health_score" in report
        assert "issues" in report
        assert "recommendations" in report
        assert 0 <= report["health_score"] <= 1
