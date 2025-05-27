"""
Integration tests for the ingestion pipeline.

This module tests the functionality of the ingestion module, which implements
the "Expand, Differentiate, Refine, Retrospect" methodology for project ingestion.
"""

import os
import pytest
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from devsynth.application.ingestion import (
    Ingestion, ArtifactType, ArtifactStatus, IngestionPhase, ProjectStructureType, IngestionMetrics
)
from devsynth.exceptions import IngestionError, ManifestError


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for the test project."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def basic_manifest_data():
    """Create basic manifest data for testing."""
    return {
        "projectName": "TestProject",
        "version": "0.1.0",
        "structure": {
            "type": "single_package",
            "directories": {
                "source": ["src"],
                "tests": ["tests"],
                "docs": ["docs"]
            }
        }
    }


@pytest.fixture
def create_manifest_file(temp_project_dir, basic_manifest_data):
    """Create a manifest.yaml file in the temporary project directory."""
    manifest_path = temp_project_dir / "manifest.yaml"
    with open(manifest_path, 'w') as f:
        yaml.dump(basic_manifest_data, f)
    return manifest_path


@pytest.fixture
def create_project_structure(temp_project_dir):
    """Create a basic project structure in the temporary directory."""
    # Create directories
    src_dir = temp_project_dir / "src"
    tests_dir = temp_project_dir / "tests"
    docs_dir = temp_project_dir / "docs"
    
    src_dir.mkdir()
    tests_dir.mkdir()
    docs_dir.mkdir()
    
    # Create some files
    (src_dir / "main.py").touch()
    (src_dir / "utils.py").touch()
    (tests_dir / "test_main.py").touch()
    (docs_dir / "README.md").touch()
    
    return temp_project_dir


class TestIngestionMetrics:
    """Tests for the IngestionMetrics class."""
    
    def test_metrics_initialization(self):
        """Test initialization of IngestionMetrics."""
        metrics = IngestionMetrics()
        
        assert metrics.artifacts_discovered == 0
        assert metrics.errors_encountered == 0
        assert metrics.warnings_generated == 0
        assert metrics.current_phase is None
        assert metrics.phase_start_time is None
        
        # Check that all artifact types and statuses are initialized to 0
        for artifact_type in ArtifactType:
            assert metrics.artifacts_by_type[artifact_type] == 0
        
        for status in ArtifactStatus:
            assert metrics.artifacts_by_status[status] == 0
    
    def test_phase_timing(self):
        """Test phase timing in IngestionMetrics."""
        metrics = IngestionMetrics()
        
        # Start a phase
        metrics.start_phase(IngestionPhase.EXPAND)
        assert metrics.current_phase == IngestionPhase.EXPAND
        assert metrics.phase_start_time is not None
        
        # End the phase
        metrics.end_phase()
        assert metrics.current_phase is None
        assert metrics.phase_start_time is None
        assert metrics.phase_durations[IngestionPhase.EXPAND] > 0
        
        # Start another phase
        metrics.start_phase(IngestionPhase.DIFFERENTIATE)
        assert metrics.current_phase == IngestionPhase.DIFFERENTIATE
        
        # Start a new phase without ending the previous one
        metrics.start_phase(IngestionPhase.REFINE)
        assert metrics.current_phase == IngestionPhase.REFINE
        assert metrics.phase_durations[IngestionPhase.DIFFERENTIATE] > 0
    
    def test_complete_metrics(self):
        """Test completing metrics collection."""
        metrics = IngestionMetrics()
        
        # Start a phase
        metrics.start_phase(IngestionPhase.EXPAND)
        
        # Complete metrics
        metrics.complete()
        
        assert metrics.current_phase is None
        assert metrics.phase_start_time is None
        assert metrics.end_time is not None
        assert metrics.phase_durations[IngestionPhase.EXPAND] > 0
    
    def test_get_summary(self):
        """Test getting a summary of metrics."""
        metrics = IngestionMetrics()
        
        # Add some data
        metrics.artifacts_discovered = 10
        metrics.errors_encountered = 2
        metrics.warnings_generated = 3
        metrics.artifacts_by_type[ArtifactType.CODE] = 5
        metrics.artifacts_by_type[ArtifactType.TEST] = 3
        metrics.artifacts_by_status[ArtifactStatus.NEW] = 8
        metrics.artifacts_by_status[ArtifactStatus.CHANGED] = 2
        
        # Start and end a phase
        metrics.start_phase(IngestionPhase.EXPAND)
        metrics.end_phase()
        
        # Get summary
        summary = metrics.get_summary()
        
        assert summary["artifacts"]["total"] == 10
        assert summary["artifacts"]["by_type"]["CODE"] == 5
        assert summary["artifacts"]["by_type"]["TEST"] == 3
        assert summary["artifacts"]["by_status"]["NEW"] == 8
        assert summary["artifacts"]["by_status"]["CHANGED"] == 2
        assert summary["errors"] == 2
        assert summary["warnings"] == 3
        assert "duration_seconds" in summary
        assert "phases" in summary
        assert "EXPAND" in summary["phases"]


class TestIngestion:
    """Tests for the Ingestion class."""
    
    def test_initialization(self, temp_project_dir, create_manifest_file):
        """Test initialization of the Ingestion class."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        
        assert ingestion.project_root == temp_project_dir
        assert ingestion.manifest_path == create_manifest_file
        assert isinstance(ingestion.metrics, IngestionMetrics)
        assert isinstance(ingestion.project_graph, object)
        assert ingestion.manifest_data is None
        assert ingestion.previous_state is None
        assert isinstance(ingestion.artifacts, dict)
        assert ingestion.project_structure is None
    
    def test_initialization_with_nonexistent_project_root(self):
        """Test initialization with a non-existent project root."""
        with pytest.raises(IngestionError):
            Ingestion("/nonexistent/path")
    
    def test_load_manifest(self, temp_project_dir, create_manifest_file, basic_manifest_data):
        """Test loading the manifest file."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        manifest_data = ingestion.load_manifest()
        
        assert manifest_data == basic_manifest_data
        assert ingestion.manifest_data == basic_manifest_data
        assert ingestion.project_structure == ProjectStructureType.STANDARD
    
    def test_load_manifest_file_not_found(self, temp_project_dir):
        """Test loading a non-existent manifest file."""
        ingestion = Ingestion(temp_project_dir, temp_project_dir / "nonexistent.yaml")
        
        with pytest.raises(ManifestError):
            ingestion.load_manifest()
    
    def test_load_manifest_invalid_yaml(self, temp_project_dir):
        """Test loading an invalid YAML manifest file."""
        # Create an invalid YAML file
        manifest_path = temp_project_dir / "manifest.yaml"
        with open(manifest_path, 'w') as f:
            f.write("invalid: yaml: content:\n  - missing colon\n")
        
        ingestion = Ingestion(temp_project_dir, manifest_path)
        
        with pytest.raises(ManifestError):
            ingestion.load_manifest()
    
    def test_load_manifest_missing_required_fields(self, temp_project_dir):
        """Test loading a manifest file with missing required fields."""
        # Create a manifest with missing required fields
        manifest_path = temp_project_dir / "manifest.yaml"
        with open(manifest_path, 'w') as f:
            yaml.dump({"projectName": "TestProject"}, f)  # Missing structure field
        
        ingestion = Ingestion(temp_project_dir, manifest_path)
        
        with pytest.raises(ManifestError):
            ingestion.load_manifest()
    
    @patch('devsynth.domain.project_model.ProjectModel')
    def test_run_ingestion(self, mock_project_model, temp_project_dir, create_manifest_file, create_project_structure):
        """Test running the full ingestion process."""
        # Setup mock
        mock_instance = MagicMock()
        mock_project_model.return_value = mock_instance
        mock_instance.to_dict.return_value = {
            "artifacts": {
                "/test/path/file.py": {
                    "name": "file.py",
                    "type": "CODE",
                    "is_directory": False,
                    "metadata": {}
                }
            },
            "relationships": [
                {"source": "/test/path", "target": "/test/path/file.py", "metadata": {"relationship": "contains"}}
            ]
        }
        
        # Run ingestion
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        result = ingestion.run_ingestion(verbose=True)
        
        # Verify the result
        assert result["success"] is True
        assert "metrics" in result
        assert "artifacts" in result
        assert result["artifacts"]["total"] == 1
        assert "project_structure" in result
        
        # Verify that all phases were run
        mock_project_model.assert_called_once()
        mock_instance.build_model.assert_called_once()
    
    @patch('devsynth.domain.project_model.ProjectModel')
    def test_run_ingestion_with_error(self, mock_project_model, temp_project_dir, create_manifest_file):
        """Test running ingestion with an error."""
        # Setup mock to raise an error
        mock_project_model.side_effect = Exception("Test error")
        
        # Run ingestion
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        result = ingestion.run_ingestion()
        
        # Verify the result
        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]
        assert "metrics" in result
        assert result["metrics"]["errors"] == 1
    
    @patch('devsynth.domain.project_model.ProjectModel')
    def test_expand_phase(self, mock_project_model, temp_project_dir, create_manifest_file):
        """Test the Expand phase of the ingestion process."""
        # Setup mock
        mock_instance = MagicMock()
        mock_project_model.return_value = mock_instance
        mock_instance.to_dict.return_value = {
            "artifacts": {
                "/test/path/file.py": {
                    "name": "file.py",
                    "type": "CODE",
                    "is_directory": False,
                    "metadata": {}
                }
            },
            "relationships": [
                {"source": "/test/path", "target": "/test/path/file.py", "metadata": {"relationship": "contains"}}
            ]
        }
        
        # Run ingestion with just the expand phase
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        ingestion._run_expand_phase(False, True)
        
        # Verify the results
        assert len(ingestion.artifacts) == 1
        assert "/test/path/file.py" in ingestion.artifacts
        assert ingestion.metrics.artifacts_discovered == 1
        assert ingestion.metrics.artifacts_by_status[ArtifactStatus.NEW] == 1
        
        # Verify that the project model was built
        mock_project_model.assert_called_once_with(temp_project_dir, ingestion.manifest_data)
        mock_instance.build_model.assert_called_once()
    
    def test_differentiate_phase(self, temp_project_dir, create_manifest_file):
        """Test the Differentiate phase of the ingestion process."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        
        # Add some artifacts
        ingestion.artifacts = {
            str(temp_project_dir / "src" / "file.py"): {
                "name": "file.py",
                "type": "CODE",
                "is_directory": False,
                "metadata": {}
            }
        }
        
        # Run the differentiate phase
        ingestion._run_differentiate_phase(False, True)
        
        # Verify that the phase ran without errors
        assert ingestion.metrics.phase_durations[IngestionPhase.DIFFERENTIATE] > 0
    
    def test_refine_phase(self, temp_project_dir, create_manifest_file):
        """Test the Refine phase of the ingestion process."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        
        # Add some artifacts
        ingestion.artifacts = {
            str(temp_project_dir / "src" / "file.py"): {
                "name": "file.py",
                "type": "CODE",
                "is_directory": False,
                "metadata": {}
            }
        }
        
        # Run the refine phase
        ingestion._run_refine_phase(True, True)  # Use dry_run=True to avoid file operations
        
        # Verify that the phase ran without errors
        assert ingestion.metrics.phase_durations[IngestionPhase.REFINE] > 0
    
    def test_retrospect_phase(self, temp_project_dir, create_manifest_file):
        """Test the Retrospect phase of the ingestion process."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        
        # Add some artifacts
        ingestion.artifacts = {
            str(temp_project_dir / "src" / "file.py"): {
                "name": "file.py",
                "type": "CODE",
                "is_directory": False,
                "metadata": {}
            }
        }
        
        # Run the retrospect phase
        ingestion._run_retrospect_phase(True, True)  # Use dry_run=True to avoid file operations
        
        # Verify that the phase ran without errors
        assert ingestion.metrics.phase_durations[IngestionPhase.RETROSPECT] > 0
    
    def test_evaluate_ingestion_process(self, temp_project_dir, create_manifest_file):
        """Test evaluating the ingestion process."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        
        # Set up metrics
        ingestion.metrics.artifacts_discovered = 10
        ingestion.metrics.errors_encountered = 0
        ingestion.metrics.warnings_generated = 2
        ingestion.metrics.phase_durations[IngestionPhase.EXPAND] = 1.0
        ingestion.metrics.phase_durations[IngestionPhase.DIFFERENTIATE] = 0.5
        ingestion.metrics.phase_durations[IngestionPhase.REFINE] = 0.3
        ingestion.metrics.phase_durations[IngestionPhase.RETROSPECT] = 0.2
        
        # Evaluate the process
        evaluation = ingestion._evaluate_ingestion_process(True)
        
        # Verify the evaluation
        assert evaluation["success"] is True
        assert evaluation["artifacts_discovered"] == 10
        assert evaluation["errors"] == 0
        assert evaluation["warnings"] == 2
        assert "phase_durations" in evaluation
        assert "phase_percentages" in evaluation
        assert "overall_assessment" in evaluation
    
    def test_identify_improvement_areas(self, temp_project_dir, create_manifest_file):
        """Test identifying improvement areas."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        
        # Set up metrics
        ingestion.metrics.artifacts_by_type[ArtifactType.CODE] = 10
        ingestion.metrics.artifacts_by_type[ArtifactType.TEST] = 0
        
        # Identify improvement areas
        improvements = ingestion._identify_improvement_areas(True)
        
        # Verify improvements
        assert len(improvements) > 0
        assert any(imp["area"] == "Testing" for imp in improvements)
    
    def test_generate_recommendations(self, temp_project_dir, create_manifest_file):
        """Test generating recommendations."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.project_structure = ProjectStructureType.STANDARD
        
        # Generate recommendations
        recommendations = ingestion._generate_recommendations(True)
        
        # Verify recommendations
        assert len(recommendations) > 0
        assert any(rec["category"] == "Manifest" for rec in recommendations)
    
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.dump')
    def test_save_refined_data(self, mock_json_dump, mock_open, temp_project_dir, create_manifest_file):
        """Test saving refined data."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        
        # Create test data
        refined_data = {
            "project_root": str(temp_project_dir),
            "manifest_path": str(create_manifest_file),
            "artifacts": {"test": "data"},
            "metrics": {"test": "metrics"}
        }
        
        # Mock os.makedirs to avoid creating directories
        with patch('os.makedirs'):
            ingestion._save_refined_data(refined_data, True)
        
        # Verify that open was called twice (once for refined data, once for previous state)
        assert mock_open.call_count == 2
        
        # Verify that json.dump was called twice
        assert mock_json_dump.call_count == 2
    
    @patch('builtins.open', new_callable=MagicMock)
    def test_generate_markdown_summary(self, mock_open, temp_project_dir, create_manifest_file):
        """Test generating a markdown summary."""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        
        # Create test data
        retrospective = {
            "project_root": str(temp_project_dir),
            "evaluation": {"overall_assessment": "Good"},
            "metrics": {"duration_seconds": 2.5, "artifacts": {"total": 10}, "errors": 0, "warnings": 2},
            "improvements": [{"area": "Testing", "issue": "No tests", "recommendation": "Add tests"}],
            "recommendations": [{"category": "Code", "priority": "High", "recommendation": "Refactor"}]
        }
        
        # Generate markdown summary
        ingestion._generate_markdown_summary(retrospective, Path("test_output.md"))
        
        # Verify that open was called
        mock_open.assert_called_once()
        
        # Verify that write was called multiple times
        file_handle = mock_open.return_value.__enter__.return_value
        assert file_handle.write.call_count > 10