"""
Unit tests for the ingest_cmd module.

This module tests the functionality of the ingest_cmd module, which provides
the 'devsynth ingest' CLI command for ingesting a project into DevSynth.
"""
import os
import sys
import types
import pytest
import yaml
pytest.skip('Ingestion CLI tests are currently incompatible',
    allow_module_level=True)
from pathlib import Path
from unittest.mock import patch, MagicMock, call
sys.modules.setdefault('typer', types.ModuleType('typer'))
sys.modules.setdefault('duckdb', types.ModuleType('duckdb'))
import importlib.util
from devsynth.exceptions import ManifestError, IngestionError
spec = importlib.util.spec_from_file_location('ingest_cmd', Path(__file__).
    parents[2] / 'src' / 'devsynth' / 'application' / 'cli' / 'ingest_cmd.py')
ingest_cmd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_cmd)
sys.modules.setdefault('devsynth.application.cli.ingest_cmd', ingest_cmd)
cli_pkg = sys.modules.setdefault('devsynth.application.cli', types.
    ModuleType('cli'))
setattr(cli_pkg, 'ingest_cmd', ingest_cmd)
ingest_cmd_fn = ingest_cmd.ingest_cmd
validate_manifest = ingest_cmd.validate_manifest
load_manifest = ingest_cmd.load_manifest
expand_phase = ingest_cmd.expand_phase
differentiate_phase = ingest_cmd.differentiate_phase
refine_phase = ingest_cmd.refine_phase
retrospect_phase = ingest_cmd.retrospect_phase


@pytest.fixture
def mock_bridge():
    """Mock the UX bridge to capture output."""
    ingest_cmd.bridge = MagicMock()
    yield ingest_cmd.bridge


@pytest.fixture
def mock_validate_manifest():
    """Mock the validate_manifest function."""
    with patch('devsynth.application.cli.ingest_cmd.validate_manifest'
        ) as mock:
        yield mock


@pytest.fixture
def mock_load_manifest():
    """Mock the load_manifest function."""
    with patch('devsynth.application.cli.ingest_cmd.load_manifest') as mock:
        mock.return_value = {'projectName': 'TestProject', 'version': '0.1.0'}
        yield mock


@pytest.fixture
def mock_ingestion():
    """Mock the Ingestion class used within ingest_cmd."""
    with patch('devsynth.application.cli.ingest_cmd.Ingestion') as cls:
        instance = MagicMock()
        instance.run_ingestion.return_value = {'success': True, 'metrics':
            {'duration_seconds': 1}}
        cls.return_value = instance
        yield cls


@pytest.fixture
def mock_memory_manager():
    """Mock MemoryManager used in phase helpers."""
    with patch('devsynth.application.cli.ingest_cmd.MemoryManager') as cls:
        instance = MagicMock()
        cls.return_value = instance
        yield instance


class TestIngestCmd:
    """Tests for the ingest_cmd function.

ReqID: N/A"""

    def test_ingest_cmd_with_defaults_succeeds(self, mock_bridge,
        mock_validate_manifest, mock_load_manifest, mock_ingestion):
        """Test ingest_cmd with default arguments.

ReqID: N/A"""
        ingest_cmd_fn()
        mock_validate_manifest.assert_called_once()
        mock_load_manifest.assert_called_once()
        mock_ingestion.return_value.run_ingestion.assert_called_once()
        assert mock_bridge.print.call_count >= 5

    def test_ingest_cmd_with_custom_manifest_succeeds(self, mock_bridge,
        mock_validate_manifest, mock_load_manifest):
        """Test ingest_cmd with a custom manifest path.

ReqID: N/A"""
        custom_path = 'custom/manifest.yaml'
        ingest_cmd_fn(manifest_path=custom_path, validate_only=True)
        mock_validate_manifest.assert_called_once()
        args, _ = mock_validate_manifest.call_args
        assert str(args[0]) == custom_path
        mock_load_manifest.assert_not_called()

    def test_ingest_cmd_dry_run_succeeds(self, mock_bridge,
        mock_validate_manifest, mock_load_manifest, mock_ingestion):
        """Test ingest_cmd with dry_run=True.

ReqID: N/A"""
        ingest_cmd_fn(dry_run=True)
        mock_validate_manifest.assert_called_once()
        mock_load_manifest.assert_called_once()
        mock_ingestion.return_value.run_ingestion.assert_called_once_with(
            dry_run=True, verbose=False)

    def test_ingest_cmd_validate_only_is_valid(self, mock_bridge,
        mock_validate_manifest, mock_load_manifest):
        """Test ingest_cmd with validate_only=True.

ReqID: N/A"""
        ingest_cmd_fn(validate_only=True)
        mock_validate_manifest.assert_called_once()
        mock_load_manifest.assert_not_called()

    def test_ingest_cmd_verbose_succeeds(self, mock_bridge,
        mock_validate_manifest, mock_load_manifest, mock_ingestion):
        """Test ingest_cmd with verbose=True.

ReqID: N/A"""
        ingest_cmd_fn(verbose=True)
        mock_validate_manifest.assert_called_once_with(Path(os.path.join(os
            .getcwd(), 'manifest.yaml')), True)
        mock_ingestion.return_value.run_ingestion.assert_called_once_with(
            dry_run=False, verbose=True)

    def test_ingest_cmd_manifest_error_raises_error(self, mock_bridge,
        mock_validate_manifest):
        """Test ingest_cmd with a ManifestError.

ReqID: N/A"""
        mock_validate_manifest.side_effect = ManifestError(
            'Test manifest error')
        with pytest.raises(SystemExit) as excinfo:
            ingest_cmd_fn()
        assert excinfo.value.code == 1
        mock_bridge.print.assert_called_once_with(
            '[red]Manifest Error:[/red] Test manifest error')

    def test_ingest_cmd_ingestion_error_raises_error(self, mock_bridge,
        mock_validate_manifest, mock_load_manifest, mock_ingestion):
        """Test ingest_cmd with an IngestionError.

ReqID: N/A"""
        mock_ingestion.return_value.run_ingestion.side_effect = IngestionError(
            'Test ingestion error')
        mock_bridge.reset_mock()
        with pytest.raises(SystemExit) as excinfo:
            ingest_cmd_fn()
        assert excinfo.value.code == 1
        assert mock_bridge.print.call_count >= 1
        mock_bridge.print.assert_any_call(
            '[red]Ingestion Error:[/red] Test ingestion error')


class TestValidateManifest:
    """Tests for the validate_manifest function.

ReqID: N/A"""

    @patch('devsynth.application.cli.ingest_cmd.sys')
    @patch('devsynth.application.cli.ingest_cmd.Path')
    def test_validate_manifest_success_is_valid(self, mock_path, mock_sys,
        mock_bridge):
        """Test validate_manifest with a valid manifest.

ReqID: N/A"""
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True
        mock_parent = MagicMock()
        mock_manifest_path.parent = mock_parent
        mock_docs_dir = MagicMock()
        mock_parent.__truediv__.return_value = mock_docs_dir
        mock_schema_path = MagicMock()
        mock_schema_path.exists.return_value = True
        mock_docs_dir.__truediv__.return_value = mock_schema_path
        (mock_path.return_value.parent.parent.parent.parent.parent.
            __truediv__.return_value) = 'scripts_dir'
        mock_sys.path = MagicMock()
        mock_validate_manifest_script = MagicMock(return_value=True)
        with patch.dict('sys.modules', {'validate_manifest': MagicMock(
            validate_manifest=mock_validate_manifest_script)}):
            validate_manifest(mock_manifest_path, verbose=True)
            mock_sys.path.append.assert_called_once_with('scripts_dir')
            mock_validate_manifest_script.assert_called_once_with(
                mock_manifest_path, mock_schema_path, mock_parent)
            mock_bridge.print.assert_called_once_with(
                '[green]Manifest validation successful.[/green]')

    def test_validate_manifest_file_not_found_is_valid(self):
        """Test validate_manifest with a non-existent manifest file.

ReqID: N/A"""
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = False
        with pytest.raises(ManifestError) as excinfo:
            validate_manifest(mock_manifest_path)
        assert 'Manifest file not found' in str(excinfo.value)

    @patch('devsynth.application.cli.ingest_cmd.sys')
    @patch('devsynth.application.cli.ingest_cmd.Path')
    def test_validate_manifest_schema_not_found_is_valid(self, mock_path,
        mock_sys):
        """Test validate_manifest with a non-existent schema file.

ReqID: N/A"""
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True
        mock_parent = MagicMock()
        mock_manifest_path.parent = mock_parent
        mock_docs_dir = MagicMock()
        mock_parent.__truediv__.return_value = mock_docs_dir
        mock_schema_path = MagicMock()
        mock_schema_path.exists.return_value = False
        mock_docs_dir.__truediv__.return_value = mock_schema_path
        (mock_path.return_value.parent.parent.parent.parent.parent.
            __truediv__.return_value) = 'scripts_dir'
        mock_sys.path = MagicMock()
        mock_validate_module = MagicMock()
        mock_validate_module.validate_manifest = MagicMock()
        with patch.dict('sys.modules', {'validate_manifest':
            mock_validate_module}):
            with pytest.raises(ManifestError) as excinfo:
                validate_manifest(mock_manifest_path)
            mock_sys.path.append.assert_called_once_with('scripts_dir')
            assert 'Manifest schema file not found' in str(excinfo.value)

    @patch('devsynth.application.cli.ingest_cmd.sys')
    @patch('devsynth.application.cli.ingest_cmd.Path')
    def test_validate_manifest_validation_failed_fails(self, mock_path,
        mock_sys):
        """Test validate_manifest with a validation failure.

ReqID: N/A"""
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True
        mock_parent = MagicMock()
        mock_manifest_path.parent = mock_parent
        mock_docs_dir = MagicMock()
        mock_parent.__truediv__.return_value = mock_docs_dir
        mock_schema_path = MagicMock()
        mock_schema_path.exists.return_value = True
        mock_docs_dir.__truediv__.return_value = mock_schema_path
        (mock_path.return_value.parent.parent.parent.parent.parent.
            __truediv__.return_value) = 'scripts_dir'
        mock_sys.path = MagicMock()
        mock_validate_module = MagicMock()
        mock_validate_module.validate_manifest = MagicMock(return_value=False)
        with patch.dict('sys.modules', {'validate_manifest':
            mock_validate_module}):
            with pytest.raises(ManifestError) as excinfo:
                validate_manifest(mock_manifest_path)
            mock_sys.path.append.assert_called_once_with('scripts_dir')
            mock_validate_module.validate_manifest.assert_called_once_with(
                mock_manifest_path, mock_schema_path, mock_parent)
            assert 'Manifest validation failed' in str(excinfo.value)


class TestLoadManifest:
    """Tests for the load_manifest function.

ReqID: N/A"""

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_manifest_success_is_valid(self, mock_yaml_load, mock_open):
        """Test load_manifest with a valid manifest.

ReqID: N/A"""
        mock_yaml_load.return_value = {'projectName': 'TestProject',
            'version': '0.1.0'}
        result = load_manifest(Path('manifest.yaml'))
        assert result == {'projectName': 'TestProject', 'version': '0.1.0'}
        mock_open.assert_called_once_with(Path('manifest.yaml'), 'r')
        mock_yaml_load.assert_called_once()

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_manifest_yaml_error_raises_error(self, mock_yaml_load,
        mock_open):
        """Test load_manifest with a YAML parsing error.

ReqID: N/A"""
        mock_yaml_load.side_effect = yaml.YAMLError('Test YAML error')
        with pytest.raises(ManifestError) as excinfo:
            load_manifest(Path('manifest.yaml'))
        assert 'Failed to parse manifest YAML' in str(excinfo.value)

    @patch('builtins.open')
    def test_load_manifest_file_error_raises_error(self, mock_open):
        """Test load_manifest with a file opening error.

ReqID: N/A"""
        mock_open.side_effect = FileNotFoundError('Test file error')
        with pytest.raises(ManifestError) as excinfo:
            load_manifest(Path('manifest.yaml'))
        assert 'Failed to load manifest' in str(excinfo.value)


class TestPhases:
    """Tests for the phase functions.

ReqID: N/A"""

    def test_expand_phase_has_expected(self, mock_bridge, mock_memory_manager):
        """Test expand_phase function.

ReqID: N/A"""
        mock_memory_manager.reset_mock()
        result = expand_phase({'projectName': 'TestProject'}, verbose=True,
            bridge=mock_bridge)
        assert 'artifacts_discovered' in result
        assert 'files_processed' in result
        assert 'duration_seconds' in result
        assert mock_bridge.print.call_count >= 3
        mock_memory_manager.store_with_edrr_phase.assert_called_once()

    def test_differentiate_phase_has_expected(self, mock_bridge,
        mock_memory_manager):
        """Test differentiate_phase function.

ReqID: N/A"""
        mock_memory_manager.reset_mock()
        result = differentiate_phase({'projectName': 'TestProject'}, {
            'artifacts_discovered': 150}, verbose=True, bridge=mock_bridge)
        assert 'inconsistencies_found' in result
        assert 'gaps_identified' in result
        assert 'duration_seconds' in result
        assert mock_bridge.print.call_count >= 3
        mock_memory_manager.store_with_edrr_phase.assert_called_once()

    def test_refine_phase_has_expected(self, mock_bridge, mock_memory_manager):
        """Test refine_phase function.

ReqID: N/A"""
        mock_memory_manager.reset_mock()
        result = refine_phase({'projectName': 'TestProject'}, {
            'inconsistencies_found': 10}, verbose=True, bridge=mock_bridge)
        assert 'relationships_created' in result
        assert 'outdated_items_archived' in result
        assert 'duration_seconds' in result
        assert mock_bridge.print.call_count >= 2
        mock_memory_manager.store_with_edrr_phase.assert_called_once()

    def test_retrospect_phase_has_expected(self, mock_bridge,
        mock_memory_manager):
        """Test retrospect_phase function.

ReqID: N/A"""
        mock_memory_manager.reset_mock()
        result = retrospect_phase({'projectName': 'TestProject'}, {
            'relationships_created': 75}, verbose=True, bridge=mock_bridge)
        assert 'insights_captured' in result
        assert 'improvements_identified' in result
        assert 'duration_seconds' in result
        assert mock_bridge.print.call_count >= 1
        mock_memory_manager.store_with_edrr_phase.assert_called_once()
