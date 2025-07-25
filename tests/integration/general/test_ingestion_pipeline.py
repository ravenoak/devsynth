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
from devsynth.application.ingestion import Ingestion, ArtifactType, ArtifactStatus, IngestionPhase, ProjectStructureType, IngestionMetrics
from devsynth.exceptions import IngestionError, ManifestError


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for the test project."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def basic_manifest_data():
    """Create basic manifest data for testing."""
    return {'metadata': {'projectName': 'TestProject', 'version': '0.1.0'},
        'structure': {'type': 'single_package', 'directories': {'source': [
        'src'], 'tests': ['tests'], 'docs': ['docs']}}}


@pytest.fixture
def create_manifest_file(temp_project_dir, basic_manifest_data):
    """Create a manifest.yaml file in the temporary project directory."""
    manifest_path = temp_project_dir / 'manifest.yaml'
    with open(manifest_path, 'w') as f:
        yaml.dump(basic_manifest_data, f)
    return manifest_path


@pytest.fixture
def create_project_structure(temp_project_dir):
    """Create a basic project structure in the temporary directory."""
    src_dir = temp_project_dir / 'src'
    tests_dir = temp_project_dir / 'tests'
    docs_dir = temp_project_dir / 'docs'
    src_dir.mkdir()
    tests_dir.mkdir()
    docs_dir.mkdir()
    (src_dir / 'main.py').touch()
    (src_dir / 'utils.py').touch()
    (tests_dir / 'test_main.py').touch()
    (docs_dir / 'README.md').touch()
    return temp_project_dir


class TestIngestionMetrics:
    """Tests for the IngestionMetrics class.

ReqID: N/A"""

    def test_metrics_initialization_succeeds(self):
        """Test initialization of IngestionMetrics.

ReqID: N/A"""
        metrics = IngestionMetrics()
        assert metrics.artifacts_discovered == 0
        assert metrics.errors_encountered == 0
        assert metrics.warnings_generated == 0
        assert metrics.current_phase is None
        assert metrics.phase_start_time is None
        for artifact_type in ArtifactType:
            assert metrics.artifacts_by_type[artifact_type] == 0
        for status in ArtifactStatus:
            assert metrics.artifacts_by_status[status] == 0

    def test_phase_timing_has_expected(self):
        """Test phase timing in IngestionMetrics.

ReqID: N/A"""
        metrics = IngestionMetrics()
        metrics.start_phase(IngestionPhase.EXPAND)
        assert metrics.current_phase == IngestionPhase.EXPAND
        assert metrics.phase_start_time is not None
        metrics.end_phase()
        assert metrics.current_phase is None
        assert metrics.phase_start_time is None
        assert metrics.phase_durations[IngestionPhase.EXPAND] > 0
        metrics.start_phase(IngestionPhase.DIFFERENTIATE)
        assert metrics.current_phase == IngestionPhase.DIFFERENTIATE
        metrics.start_phase(IngestionPhase.REFINE)
        assert metrics.current_phase == IngestionPhase.REFINE
        assert metrics.phase_durations[IngestionPhase.DIFFERENTIATE] > 0

    def test_complete_metrics_succeeds(self):
        """Test completing metrics collection.

ReqID: N/A"""
        metrics = IngestionMetrics()
        metrics.start_phase(IngestionPhase.EXPAND)
        metrics.complete()
        assert metrics.current_phase is None
        assert metrics.phase_start_time is None
        assert metrics.end_time is not None
        assert metrics.phase_durations[IngestionPhase.EXPAND] > 0

    def test_get_summary_succeeds(self):
        """Test getting a summary of metrics.

ReqID: N/A"""
        metrics = IngestionMetrics()
        metrics.artifacts_discovered = 10
        metrics.errors_encountered = 2
        metrics.warnings_generated = 3
        metrics.artifacts_by_type[ArtifactType.CODE] = 5
        metrics.artifacts_by_type[ArtifactType.TEST] = 3
        metrics.artifacts_by_status[ArtifactStatus.NEW] = 8
        metrics.artifacts_by_status[ArtifactStatus.CHANGED] = 2
        metrics.start_phase(IngestionPhase.EXPAND)
        metrics.end_phase()
        summary = metrics.get_summary()
        assert summary['artifacts']['total'] == 10
        assert summary['artifacts']['by_type']['CODE'] == 5
        assert summary['artifacts']['by_type']['TEST'] == 3
        assert summary['artifacts']['by_status']['NEW'] == 8
        assert summary['artifacts']['by_status']['CHANGED'] == 2
        assert summary['errors'] == 2
        assert summary['warnings'] == 3
        assert 'duration_seconds' in summary
        assert 'phases' in summary
        assert 'EXPAND' in summary['phases']


class TestIngestion:
    """Tests for the Ingestion class.

ReqID: N/A"""

    def test_initialization_succeeds(self, temp_project_dir,
        create_manifest_file):
        """Test initialization of the Ingestion class.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        assert str(ingestion.project_root) == str(temp_project_dir.resolve())
        assert ingestion.manifest_path == create_manifest_file
        assert isinstance(ingestion.metrics, IngestionMetrics)
        assert isinstance(ingestion.project_graph, object)
        assert ingestion.manifest_data is None
        assert ingestion.previous_state is None
        assert isinstance(ingestion.artifacts, dict)
        assert ingestion.project_structure is None

    def test_initialization_with_nonexistent_project_root_succeeds(self):
        """Test initialization with a non-existent project root.

ReqID: N/A"""
        with pytest.raises(IngestionError):
            Ingestion('/nonexistent/path')

    def test_load_manifest_succeeds(self, temp_project_dir,
        create_manifest_file, basic_manifest_data):
        """Test loading the manifest file.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        manifest_data = ingestion.load_manifest()
        assert manifest_data == basic_manifest_data
        assert ingestion.manifest_data == basic_manifest_data
        assert ingestion.project_structure == ProjectStructureType.STANDARD

    def test_load_manifest_file_not_found_succeeds(self, temp_project_dir):
        """Test loading a non-existent manifest file.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, temp_project_dir /
            'nonexistent.yaml')
        with pytest.raises(ManifestError):
            ingestion.load_manifest()

    def test_load_manifest_invalid_yaml_is_valid(self, temp_project_dir):
        """Test loading an invalid YAML manifest file.

ReqID: N/A"""
        manifest_path = temp_project_dir / 'manifest.yaml'
        with open(manifest_path, 'w') as f:
            f.write('invalid: yaml: content:\n  - missing colon\n')
        ingestion = Ingestion(temp_project_dir, manifest_path)
        with pytest.raises(ManifestError):
            ingestion.load_manifest()

    def test_load_manifest_missing_required_fields_succeeds(self,
        temp_project_dir):
        """Test loading a manifest file with missing required fields.

ReqID: N/A"""
        manifest_path = temp_project_dir / 'manifest.yaml'
        with open(manifest_path, 'w') as f:
            yaml.dump({'projectName': 'TestProject'}, f)
        ingestion = Ingestion(temp_project_dir, manifest_path)
        with pytest.raises(ManifestError):
            ingestion.load_manifest()

    @patch('devsynth.domain.models.project.ProjectModel')
    def test_run_ingestion_succeeds(self, mock_project_model,
        temp_project_dir, create_manifest_file, create_project_structure):
        """Test running the full ingestion process.

ReqID: N/A"""
        mock_instance = MagicMock()
        mock_project_model.return_value = mock_instance
        mock_instance.to_dict.return_value = {'artifacts': {
            '/test/path/file.py': {'name': 'file.py', 'type': 'CODE',
            'is_directory': False, 'metadata': {}}}, 'relationships': [{
            'source': '/test/path', 'target': '/test/path/file.py',
            'metadata': {'relationship': 'contains'}}]}
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        result = ingestion.run_ingestion(verbose=True)
        assert result['success'] is True
        assert 'metrics' in result
        assert 'artifacts' in result
        assert result['artifacts']['total'] == 1
        assert 'project_structure' in result
        mock_project_model.assert_called_once()
        mock_instance.build_model.assert_called_once()

    @patch('devsynth.domain.models.project.ProjectModel')
    def test_run_ingestion_with_error_raises_error(self, mock_project_model,
        temp_project_dir, create_manifest_file):
        """Test running ingestion with an error.

ReqID: N/A"""
        mock_project_model.side_effect = Exception('Test error')
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        result = ingestion.run_ingestion()
        assert result['success'] is False
        assert 'error' in result
        assert 'Test error' in result['error']
        assert 'metrics' in result
        assert result['metrics']['errors'] == 2

    @patch('devsynth.domain.models.project.ProjectModel')
    def test_expand_phase_has_expected(self, mock_project_model,
        temp_project_dir, create_manifest_file):
        """Test the Expand phase of the ingestion process.

ReqID: N/A"""
        mock_instance = MagicMock()
        mock_project_model.return_value = mock_instance
        mock_instance.to_dict.return_value = {'artifacts': {
            '/test/path/file.py': {'name': 'file.py', 'type': 'CODE',
            'is_directory': False, 'metadata': {}}}, 'relationships': [{
            'source': '/test/path', 'target': '/test/path/file.py',
            'metadata': {'relationship': 'contains'}}]}
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        ingestion._run_expand_phase(False, True)
        assert len(ingestion.artifacts) == 1
        assert '/test/path/file.py' in ingestion.artifacts
        assert ingestion.metrics.artifacts_discovered == 1
        assert ingestion.metrics.artifacts_by_status[ArtifactStatus.NEW] == 1
        mock_project_model.assert_called_once()
        mock_instance.build_model.assert_called_once()

    def test_differentiate_phase_has_expected(self, temp_project_dir,
        create_manifest_file):
        """Test the Differentiate phase of the ingestion process.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        ingestion.artifacts = {str(temp_project_dir / 'src' / 'file.py'): {
            'name': 'file.py', 'type': 'CODE', 'is_directory': False,
            'metadata': {}}}
        ingestion._run_differentiate_phase(False, True)
        ingestion.metrics.end_phase()
        assert ingestion.metrics.phase_durations[IngestionPhase.DIFFERENTIATE
            ] > 0

    def test_refine_phase_has_expected(self, temp_project_dir,
        create_manifest_file):
        """Test the Refine phase of the ingestion process.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        ingestion.artifacts = {str(temp_project_dir / 'src' / 'file.py'): {
            'name': 'file.py', 'type': 'CODE', 'is_directory': False,
            'metadata': {}}}
        ingestion._run_refine_phase(True, True)
        ingestion.metrics.end_phase()
        assert ingestion.metrics.phase_durations[IngestionPhase.REFINE] > 0

    def test_retrospect_phase_has_expected(self, temp_project_dir,
        create_manifest_file):
        """Test the Retrospect phase of the ingestion process.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        ingestion.artifacts = {str(temp_project_dir / 'src' / 'file.py'): {
            'name': 'file.py', 'type': 'CODE', 'is_directory': False,
            'metadata': {}}}
        ingestion._run_retrospect_phase(True, True)
        ingestion.metrics.end_phase()
        assert ingestion.metrics.phase_durations[IngestionPhase.RETROSPECT] > 0

    def test_evaluate_ingestion_process_succeeds(self, temp_project_dir,
        create_manifest_file):
        """Test evaluating the ingestion process.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.metrics.artifacts_discovered = 10
        ingestion.metrics.errors_encountered = 0
        ingestion.metrics.warnings_generated = 2
        ingestion.metrics.phase_durations[IngestionPhase.EXPAND] = 1.0
        ingestion.metrics.phase_durations[IngestionPhase.DIFFERENTIATE] = 0.5
        ingestion.metrics.phase_durations[IngestionPhase.REFINE] = 0.3
        ingestion.metrics.phase_durations[IngestionPhase.RETROSPECT] = 0.2
        evaluation = ingestion._evaluate_ingestion_process(True)
        assert evaluation['success'] is True
        assert evaluation['artifacts_discovered'] == 10
        assert evaluation['errors'] == 0
        assert evaluation['warnings'] == 2
        assert 'phase_durations' in evaluation
        assert 'phase_percentages' in evaluation
        assert 'overall_assessment' in evaluation

    def test_identify_improvement_areas_succeeds(self, temp_project_dir,
        create_manifest_file):
        """Test identifying improvement areas.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        ingestion.metrics.artifacts_by_type[ArtifactType.CODE] = 10
        ingestion.metrics.artifacts_by_type[ArtifactType.TEST] = 0
        improvements = ingestion._identify_improvement_areas(True)
        assert len(improvements) > 0
        assert any(imp['area'] == 'Testing' for imp in improvements)

    def test_generate_recommendations_succeeds(self, temp_project_dir,
        create_manifest_file):
        """Test generating recommendations.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.project_structure = ProjectStructureType.STANDARD
        recommendations = ingestion._generate_recommendations(True)
        assert len(recommendations) > 0
        assert any(rec['category'] == 'Project Configuration' for rec in
            recommendations)

    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.dump')
    def test_save_refined_data_succeeds(self, mock_json_dump, mock_open,
        temp_project_dir, create_manifest_file):
        """Test saving refined data.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        refined_data = {'project_root': str(temp_project_dir),
            'manifest_path': str(create_manifest_file), 'artifacts': {
            'test': 'data'}, 'metrics': {'test': 'metrics'}}
        with patch('os.makedirs'):
            ingestion._save_refined_data(refined_data, True)
        assert mock_open.call_count == 2
        assert mock_json_dump.call_count == 2

    @patch('builtins.open', new_callable=MagicMock)
    def test_generate_markdown_summary_succeeds(self, mock_open,
        temp_project_dir, create_manifest_file):
        """Test generating a markdown summary.

ReqID: N/A"""
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        retrospective = {'project_root': str(temp_project_dir),
            'evaluation': {'overall_assessment': 'Good'}, 'metrics': {
            'duration_seconds': 2.5, 'artifacts': {'total': 10}, 'errors': 
            0, 'warnings': 2}, 'improvements': [{'area': 'Testing', 'issue':
            'No tests', 'recommendation': 'Add tests'}], 'recommendations':
            [{'category': 'Code', 'priority': 'High', 'recommendation':
            'Refactor'}]}
        ingestion._generate_markdown_summary(retrospective, Path(
            'test_output.md'))
        mock_open.assert_called_once()
        file_handle = mock_open.return_value.__enter__.return_value
        assert file_handle.write.call_count > 10

    @patch('devsynth.domain.models.project.ProjectModel')
    def test_full_pipeline_functions_has_expected(self, mock_project_model,
        temp_project_dir, create_manifest_file, create_project_structure):
        """Test the wrapper methods for each ingestion phase.

ReqID: N/A"""
        mock_instance = MagicMock()
        mock_project_model.return_value = mock_instance
        mock_instance.to_dict.return_value = {'artifacts': {str(
            temp_project_dir / 'src' / 'main.py'): {'name': 'main.py',
            'type': 'CODE', 'is_directory': False, 'metadata': {}}},
            'relationships': []}
        ingestion = Ingestion(temp_project_dir, create_manifest_file)
        ingestion.load_manifest()
        ingestion.edrr_coordinator.memory_manager.store_with_edrr_phase = (
            MagicMock())
        expand_res = ingestion.analyze_project_structure(True)
        assert expand_res['artifacts']
        diff_res = ingestion.validate_artifacts(True)
        assert 'status' in diff_res
        refine_res = ingestion.remove_outdated_items(True, True)
        assert 'status' in refine_res
        retro_res = ingestion.summarize_outcomes(True, True)
        assert retro_res['evaluation']['success'] is True
        assert ingestion.edrr_coordinator.memory_manager.store_with_edrr_phase.call_count == 4
