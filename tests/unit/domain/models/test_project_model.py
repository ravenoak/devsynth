"""
Unit tests for the project_model module.

This module tests the functionality of the project_model module, which defines
the domain model for representing a project's structure based on the manifest.yaml
file and file system analysis.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from devsynth.domain.models.project import (
    Artifact,
    ArtifactType,
    ProjectModel,
    ProjectStructureType,
)
from devsynth.exceptions import ProjectModelError


class TestArtifact:
    """Tests for the Artifact class.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_artifact_initialization_succeeds(self):
        """Test basic initialization of an Artifact.

        ReqID: N/A"""
        path = "/test/path/file.py"
        artifact_type = ArtifactType.CODE
        metadata = {"key": "value"}
        artifact = Artifact(path, artifact_type, metadata)
        assert str(artifact.path) == path
        assert artifact.artifact_type == artifact_type
        assert artifact.metadata == metadata
        assert artifact.name == "file.py"

    @pytest.mark.fast
    def test_artifact_str_representation_succeeds(self):
        """Test the string representation of an Artifact.

        ReqID: N/A"""
        artifact = Artifact("/test/path/file.py", ArtifactType.CODE)
        assert str(artifact) == "file.py (CODE)"

    @pytest.mark.fast
    def test_artifact_repr_representation_succeeds(self):
        """Test the repr representation of an Artifact.

        ReqID: N/A"""
        artifact = Artifact("/test/path/file.py", ArtifactType.CODE, {"key": "value"})
        assert (
            repr(artifact)
            == "Artifact(path='/test/path/file.py', type=CODE, metadata={'key': 'value'})"
        )


class TestProjectModel:
    """Tests for the ProjectModel class.

    ReqID: N/A"""

    @pytest.fixture
    def mock_project_root(self):
        """Create a mock project root path."""
        return Path("/test/project")

    @pytest.fixture
    def basic_manifest_data(self):
        """Create basic manifest data for testing."""
        return {
            "projectName": "TestProject",
            "version": "0.1.0",
            "structure": {
                "type": "single_package",
                "directories": {
                    "source": ["src"],
                    "tests": ["tests"],
                    "docs": ["docs"],
                },
            },
        }

    @pytest.fixture
    def monorepo_manifest_data(self):
        """Create monorepo manifest data for testing."""
        return {
            "projectName": "TestMonorepo",
            "version": "0.1.0",
            "structure": {
                "type": "monorepo",
                "directories": {"source": ["packages"], "docs": ["docs"]},
                "customLayouts": {
                    "type": "monorepo",
                    "packagesRoot": "packages",
                    "packages": [
                        {
                            "name": "package1",
                            "path": "package1",
                            "source": "src",
                            "tests": "tests",
                        },
                        {
                            "name": "package2",
                            "path": "package2",
                            "source": "src",
                            "tests": "tests",
                        },
                    ],
                },
            },
        }

    @pytest.mark.fast
    def test_project_model_initialization_succeeds(
        self, mock_project_root, basic_manifest_data
    ):
        """Test basic initialization of a ProjectModel.

        ReqID: N/A"""
        model = ProjectModel(mock_project_root, basic_manifest_data)
        assert model.project_root == mock_project_root
        assert model.manifest_data == basic_manifest_data
        assert model.structure_type == ProjectStructureType.STANDARD
        assert isinstance(model.graph, object)
        assert isinstance(model.artifacts, dict)
        assert len(model.artifacts) == 0

    @pytest.mark.fast
    def test_determine_structure_type_succeeds(self, mock_project_root):
        """Test determination of project structure type from manifest data.

        ReqID: N/A"""
        model = ProjectModel(
            mock_project_root, {"structure": {"type": "single_package"}}
        )
        assert model.structure_type == ProjectStructureType.STANDARD
        model = ProjectModel(mock_project_root, {"structure": {"type": "monorepo"}})
        assert model.structure_type == ProjectStructureType.MONOREPO
        model = ProjectModel(
            mock_project_root, {"structure": {"type": "multi_project_submodules"}}
        )
        assert model.structure_type == ProjectStructureType.FEDERATED
        model = ProjectModel(mock_project_root, {"structure": {"type": "custom"}})
        assert model.structure_type == ProjectStructureType.CUSTOM
        model = ProjectModel(mock_project_root, {})
        assert model.structure_type == ProjectStructureType.STANDARD

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.glob")
    @pytest.mark.fast
    def test_build_standard_model_succeeds(
        self,
        mock_glob,
        mock_is_dir,
        mock_exists,
        mock_project_root,
        basic_manifest_data,
    ):
        """Test building a model for a standard project structure.

        ReqID: N/A"""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_glob.return_value = []
        model = ProjectModel(mock_project_root, basic_manifest_data)
        model.build_model()
        assert str(mock_project_root) in model.artifacts
        assert len(model.graph.nodes) >= 1
        src_path = mock_project_root / "src"
        tests_path = mock_project_root / "tests"
        docs_path = mock_project_root / "docs"
        assert str(src_path) in model.artifacts
        assert str(tests_path) in model.artifacts
        assert str(docs_path) in model.artifacts
        assert model.artifacts[str(src_path)].artifact_type == ArtifactType.CODE
        assert model.artifacts[str(tests_path)].artifact_type == ArtifactType.TEST
        assert (
            model.artifacts[str(docs_path)].artifact_type == ArtifactType.DOCUMENTATION
        )

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.glob")
    @pytest.mark.fast
    def test_build_monorepo_model_succeeds(
        self,
        mock_glob,
        mock_is_dir,
        mock_exists,
        mock_project_root,
        monorepo_manifest_data,
    ):
        """Test building a model for a monorepo project structure.

        ReqID: N/A"""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_glob.return_value = []
        model = ProjectModel(mock_project_root, monorepo_manifest_data)
        model.build_model()
        assert str(mock_project_root) in model.artifacts
        packages_root = mock_project_root / "packages"
        package1_path = packages_root / "package1"
        package2_path = packages_root / "package2"
        assert str(packages_root) in model.artifacts
        assert str(package1_path) in model.artifacts
        assert str(package2_path) in model.artifacts
        package1_src = package1_path / "src"
        package1_tests = package1_path / "tests"
        package2_src = package2_path / "src"
        package2_tests = package2_path / "tests"
        assert str(package1_src) in model.artifacts
        assert str(package1_tests) in model.artifacts
        assert str(package2_src) in model.artifacts
        assert str(package2_tests) in model.artifacts
        assert model.artifacts[str(package1_src)].artifact_type == ArtifactType.CODE
        assert model.artifacts[str(package1_tests)].artifact_type == ArtifactType.TEST
        assert model.artifacts[str(package2_src)].artifact_type == ArtifactType.CODE
        assert model.artifacts[str(package2_tests)].artifact_type == ArtifactType.TEST

    @pytest.mark.fast
    def test_get_artifact_succeeds(self, mock_project_root, basic_manifest_data):
        """Test getting an artifact by path.

        ReqID: N/A"""
        model = ProjectModel(mock_project_root, basic_manifest_data)
        test_path = str(mock_project_root / "test_file.py")
        test_artifact = Artifact(test_path, ArtifactType.CODE)
        model.artifacts[test_path] = test_artifact
        retrieved_artifact = model.get_artifact(test_path)
        assert retrieved_artifact is test_artifact
        non_existent = model.get_artifact("/non/existent/path")
        assert non_existent is None

    @pytest.mark.fast
    def test_get_artifacts_by_type_succeeds(
        self, mock_project_root, basic_manifest_data
    ):
        """Test getting artifacts by type.

        ReqID: N/A"""
        model = ProjectModel(mock_project_root, basic_manifest_data)
        code_path1 = str(mock_project_root / "code1.py")
        code_path2 = str(mock_project_root / "code2.py")
        test_path = str(mock_project_root / "test.py")
        model.artifacts[code_path1] = Artifact(code_path1, ArtifactType.CODE)
        model.artifacts[code_path2] = Artifact(code_path2, ArtifactType.CODE)
        model.artifacts[test_path] = Artifact(test_path, ArtifactType.TEST)
        code_artifacts = model.get_artifacts_by_type(ArtifactType.CODE)
        test_artifacts = model.get_artifacts_by_type(ArtifactType.TEST)
        doc_artifacts = model.get_artifacts_by_type(ArtifactType.DOCUMENTATION)
        assert len(code_artifacts) == 2
        assert len(test_artifacts) == 1
        assert len(doc_artifacts) == 0
        assert model.artifacts[code_path1] in code_artifacts
        assert model.artifacts[code_path2] in code_artifacts
        assert model.artifacts[test_path] in test_artifacts

    @pytest.mark.fast
    def test_get_related_artifacts_succeeds(
        self, mock_project_root, basic_manifest_data
    ):
        """Test getting related artifacts.

        ReqID: N/A"""
        model = ProjectModel(mock_project_root, basic_manifest_data)
        parent_path = str(mock_project_root / "parent")
        child1_path = str(mock_project_root / "parent" / "child1")
        child2_path = str(mock_project_root / "parent" / "child2")
        model.artifacts[parent_path] = Artifact(parent_path, ArtifactType.CODE)
        model.artifacts[child1_path] = Artifact(child1_path, ArtifactType.CODE)
        model.artifacts[child2_path] = Artifact(child2_path, ArtifactType.CODE)
        model.graph.add_node(parent_path)
        model.graph.add_node(child1_path)
        model.graph.add_node(child2_path)
        model.graph.add_edge(parent_path, child1_path, relationship="contains")
        model.graph.add_edge(parent_path, child2_path, relationship="contains")
        related_to_parent = model.get_related_artifacts(parent_path)
        assert len(related_to_parent) == 2
        assert model.artifacts[child1_path] in related_to_parent
        assert model.artifacts[child2_path] in related_to_parent
        with pytest.raises(ProjectModelError):
            model.get_related_artifacts("/non/existent/path")

    @pytest.mark.fast
    def test_determine_artifact_type_succeeds(
        self, mock_project_root, basic_manifest_data
    ):
        """Test determining artifact type based on file extension and path.

        ReqID: N/A"""
        model = ProjectModel(mock_project_root, basic_manifest_data)
        assert (
            model._determine_artifact_type(Path("file.py"), ArtifactType.UNKNOWN)
            == ArtifactType.CODE
        )
        assert (
            model._determine_artifact_type(Path("file.js"), ArtifactType.UNKNOWN)
            == ArtifactType.CODE
        )
        assert (
            model._determine_artifact_type(Path("file.java"), ArtifactType.UNKNOWN)
            == ArtifactType.CODE
        )
        assert (
            model._determine_artifact_type(Path("file.md"), ArtifactType.UNKNOWN)
            == ArtifactType.DOCUMENTATION
        )
        assert (
            model._determine_artifact_type(Path("file.rst"), ArtifactType.UNKNOWN)
            == ArtifactType.DOCUMENTATION
        )
        assert (
            model._determine_artifact_type(Path("file.txt"), ArtifactType.UNKNOWN)
            == ArtifactType.DOCUMENTATION
        )
        assert (
            model._determine_artifact_type(Path("file.json"), ArtifactType.UNKNOWN)
            == ArtifactType.CONFIGURATION
        )
        assert (
            model._determine_artifact_type(Path("file.yaml"), ArtifactType.UNKNOWN)
            == ArtifactType.CONFIGURATION
        )
        assert (
            model._determine_artifact_type(Path("file.toml"), ArtifactType.UNKNOWN)
            == ArtifactType.CONFIGURATION
        )
        assert (
            model._determine_artifact_type(Path("file.sh"), ArtifactType.UNKNOWN)
            == ArtifactType.BUILD
        )
        assert (
            model._determine_artifact_type(Path("file.bat"), ArtifactType.UNKNOWN)
            == ArtifactType.BUILD
        )
        assert (
            model._determine_artifact_type(Path("test_file.py"), ArtifactType.UNKNOWN)
            == ArtifactType.TEST
        )
        assert (
            model._determine_artifact_type(Path("file_test.py"), ArtifactType.UNKNOWN)
            == ArtifactType.TEST
        )
        assert (
            model._determine_artifact_type(Path("file_spec.js"), ArtifactType.UNKNOWN)
            == ArtifactType.TEST
        )
        assert (
            model._determine_artifact_type(Path("unknown.xyz"), ArtifactType.CODE)
            == ArtifactType.CODE
        )

    @pytest.mark.fast
    def test_to_dict_succeeds(self, mock_project_root, basic_manifest_data):
        """Test converting the project model to a dictionary representation.

        ReqID: N/A"""
        model = ProjectModel(mock_project_root, basic_manifest_data)
        root_path = str(mock_project_root)
        src_path = str(mock_project_root / "src")
        file_path = str(mock_project_root / "src" / "file.py")
        model.artifacts[root_path] = Artifact(
            root_path, ArtifactType.UNKNOWN, {"is_root": True}
        )
        model.artifacts[src_path] = Artifact(
            src_path, ArtifactType.CODE, {"role": "source"}
        )
        model.artifacts[file_path] = Artifact(
            file_path, ArtifactType.CODE, {"extension": ".py"}
        )
        model.graph.add_node(root_path)
        model.graph.add_node(src_path)
        model.graph.add_node(file_path)
        model.graph.add_edge(root_path, src_path, relationship="contains")
        model.graph.add_edge(src_path, file_path, relationship="contains")
        result = model.to_dict()
        assert result["project_root"] == str(mock_project_root)
        assert result["structure_type"] == "STANDARD"
        assert len(result["artifacts"]) == 3
        assert len(result["relationships"]) == 2
        assert result["artifacts"][root_path]["type"] == "UNKNOWN"
        assert result["artifacts"][src_path]["type"] == "CODE"
        assert result["artifacts"][file_path]["type"] == "CODE"
        relationships = {
            (r["source"], r["target"]): r["metadata"] for r in result["relationships"]
        }
        assert (root_path, src_path) in relationships
        assert (src_path, file_path) in relationships
        assert relationships[root_path, src_path]["relationship"] == "contains"
        assert relationships[src_path, file_path]["relationship"] == "contains"
