"""
Unit tests for the ingest_cmd module.

This module tests the functionality of the ingest_cmd module, which provides
the 'devsynth ingest' CLI command for ingesting a project into DevSynth.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from devsynth.application.cli.ingest_cmd import (
    ingest_cmd, validate_manifest, load_manifest,
    expand_phase, differentiate_phase, refine_phase, retrospect_phase
)
from devsynth.exceptions import ManifestError, IngestionError


@pytest.fixture
def mock_console():
    """Mock the rich console to capture output."""
    with patch('devsynth.application.cli.ingest_cmd.console') as mock:
        yield mock


@pytest.fixture
def mock_validate_manifest():
    """Mock the validate_manifest function."""
    with patch('devsynth.application.cli.ingest_cmd.validate_manifest') as mock:
        yield mock


@pytest.fixture
def mock_load_manifest():
    """Mock the load_manifest function."""
    with patch('devsynth.application.cli.ingest_cmd.load_manifest') as mock:
        mock.return_value = {"projectName": "TestProject", "version": "0.1.0"}
        yield mock


@pytest.fixture
def mock_expand_phase():
    """Mock the expand_phase function."""
    with patch('devsynth.application.cli.ingest_cmd.expand_phase') as mock:
        mock.return_value = {"artifacts_discovered": 150, "files_processed": 200}
        yield mock


@pytest.fixture
def mock_differentiate_phase():
    """Mock the differentiate_phase function."""
    with patch('devsynth.application.cli.ingest_cmd.differentiate_phase') as mock:
        mock.return_value = {"inconsistencies_found": 10, "gaps_identified": 5}
        yield mock


@pytest.fixture
def mock_refine_phase():
    """Mock the refine_phase function."""
    with patch('devsynth.application.cli.ingest_cmd.refine_phase') as mock:
        mock.return_value = {"relationships_created": 75, "outdated_items_archived": 15}
        yield mock


@pytest.fixture
def mock_retrospect_phase():
    """Mock the retrospect_phase function."""
    with patch('devsynth.application.cli.ingest_cmd.retrospect_phase') as mock:
        mock.return_value = {"insights_captured": 8, "improvements_identified": 12}
        yield mock


class TestIngestCmd:
    """Tests for the ingest_cmd function."""

    def test_ingest_cmd_with_defaults(
        self, mock_console, mock_validate_manifest, mock_load_manifest,
        mock_expand_phase, mock_differentiate_phase, mock_refine_phase, mock_retrospect_phase
    ):
        """Test ingest_cmd with default arguments."""
        # Call the function
        ingest_cmd()
        
        # Verify validate_manifest was called with the default manifest path
        mock_validate_manifest.assert_called_once()
        
        # Verify load_manifest was called
        mock_load_manifest.assert_called_once()
        
        # Verify all phases were called
        mock_expand_phase.assert_called_once()
        mock_differentiate_phase.assert_called_once()
        mock_refine_phase.assert_called_once()
        mock_retrospect_phase.assert_called_once()
        
        # Verify console output
        assert mock_console.print.call_count >= 5  # At least 5 print calls

    def test_ingest_cmd_with_custom_manifest(
        self, mock_console, mock_validate_manifest, mock_load_manifest
    ):
        """Test ingest_cmd with a custom manifest path."""
        # Call the function with a custom manifest path
        custom_path = "custom/manifest.yaml"
        ingest_cmd(manifest_path=custom_path, validate_only=True)
        
        # Verify validate_manifest was called with the custom manifest path
        mock_validate_manifest.assert_called_once()
        args, _ = mock_validate_manifest.call_args
        assert str(args[0]) == custom_path
        
        # Verify load_manifest was not called (validate_only=True)
        mock_load_manifest.assert_not_called()

    def test_ingest_cmd_dry_run(
        self, mock_console, mock_validate_manifest, mock_load_manifest,
        mock_expand_phase, mock_differentiate_phase, mock_refine_phase, mock_retrospect_phase
    ):
        """Test ingest_cmd with dry_run=True."""
        # Call the function with dry_run=True
        ingest_cmd(dry_run=True)
        
        # Verify validate_manifest was called
        mock_validate_manifest.assert_called_once()
        
        # Verify load_manifest was called
        mock_load_manifest.assert_called_once()
        
        # Verify no phases were called
        mock_expand_phase.assert_not_called()
        mock_differentiate_phase.assert_not_called()
        mock_refine_phase.assert_not_called()
        mock_retrospect_phase.assert_not_called()

    def test_ingest_cmd_validate_only(
        self, mock_console, mock_validate_manifest, mock_load_manifest
    ):
        """Test ingest_cmd with validate_only=True."""
        # Call the function with validate_only=True
        ingest_cmd(validate_only=True)
        
        # Verify validate_manifest was called
        mock_validate_manifest.assert_called_once()
        
        # Verify load_manifest was not called
        mock_load_manifest.assert_not_called()

    def test_ingest_cmd_verbose(
        self, mock_console, mock_validate_manifest, mock_load_manifest,
        mock_expand_phase, mock_differentiate_phase, mock_refine_phase, mock_retrospect_phase
    ):
        """Test ingest_cmd with verbose=True."""
        # Call the function with verbose=True
        ingest_cmd(verbose=True)
        
        # Verify validate_manifest was called with verbose=True
        mock_validate_manifest.assert_called_once_with(Path(os.path.join(os.getcwd(), "manifest.yaml")), True)
        
        # Verify all phases were called with verbose=True
        mock_expand_phase.assert_called_once_with(mock_load_manifest.return_value, True)
        mock_differentiate_phase.assert_called_once_with(mock_load_manifest.return_value, mock_expand_phase.return_value, True)
        mock_refine_phase.assert_called_once_with(mock_load_manifest.return_value, mock_differentiate_phase.return_value, True)
        mock_retrospect_phase.assert_called_once_with(mock_load_manifest.return_value, mock_refine_phase.return_value, True)

    def test_ingest_cmd_manifest_error(self, mock_console, mock_validate_manifest):
        """Test ingest_cmd with a ManifestError."""
        # Set up the mock to raise a ManifestError
        mock_validate_manifest.side_effect = ManifestError("Test manifest error")
        
        # Call the function and verify it exits with an error
        with pytest.raises(SystemExit) as excinfo:
            ingest_cmd()
        
        assert excinfo.value.code == 1
        
        # Verify console output
        mock_console.print.assert_called_once_with("[red]Manifest Error:[/red] Test manifest error")

    def test_ingest_cmd_ingestion_error(self, mock_console, mock_validate_manifest, mock_load_manifest, mock_expand_phase):
        """Test ingest_cmd with an IngestionError."""
        # Set up the mock to raise an IngestionError
        mock_expand_phase.side_effect = IngestionError("Test ingestion error")
        
        # Call the function and verify it exits with an error
        with pytest.raises(SystemExit) as excinfo:
            ingest_cmd()
        
        assert excinfo.value.code == 1
        
        # Verify console output
        mock_console.print.assert_called_once_with("[red]Ingestion Error:[/red] Test ingestion error")


class TestValidateManifest:
    """Tests for the validate_manifest function."""

    @patch('devsynth.application.cli.ingest_cmd.sys.path.append')
    @patch('devsynth.application.cli.ingest_cmd.Path')
    def test_validate_manifest_success(self, mock_path, mock_append, mock_console):
        """Test validate_manifest with a valid manifest."""
        # Set up mocks
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True
        mock_manifest_path.parent = "project_root"
        
        mock_schema_path = MagicMock()
        mock_schema_path.exists.return_value = True
        
        mock_path.return_value.parent.parent.parent.parent.parent.__truediv__.return_value = "scripts_dir"
        mock_path.return_value.__truediv__.return_value = mock_schema_path
        
        # Mock the imported validate_manifest function
        mock_validate_manifest_script = MagicMock(return_value=True)
        
        # Mock the import
        with patch.dict('sys.modules', {'validate_manifest': MagicMock(validate_manifest=mock_validate_manifest_script)}):
            # Call the function
            validate_manifest(mock_manifest_path, verbose=True)
            
            # Verify the script was called
            mock_validate_manifest_script.assert_called_once_with(mock_manifest_path, mock_schema_path, "project_root")
            
            # Verify console output
            mock_console.print.assert_called_once_with("[green]Manifest validation successful.[/green]")

    def test_validate_manifest_file_not_found(self):
        """Test validate_manifest with a non-existent manifest file."""
        # Set up mock
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = False
        
        # Call the function and verify it raises an error
        with pytest.raises(ManifestError) as excinfo:
            validate_manifest(mock_manifest_path)
        
        assert "Manifest file not found" in str(excinfo.value)

    @patch('devsynth.application.cli.ingest_cmd.sys.path.append')
    @patch('devsynth.application.cli.ingest_cmd.Path')
    def test_validate_manifest_schema_not_found(self, mock_path, mock_append):
        """Test validate_manifest with a non-existent schema file."""
        # Set up mocks
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True
        mock_manifest_path.parent = "project_root"
        
        mock_schema_path = MagicMock()
        mock_schema_path.exists.return_value = False
        
        mock_path.return_value.parent.parent.parent.parent.parent.__truediv__.return_value = "scripts_dir"
        mock_path.return_value.__truediv__.return_value = mock_schema_path
        
        # Call the function and verify it raises an error
        with pytest.raises(ManifestError) as excinfo:
            validate_manifest(mock_manifest_path)
        
        assert "Manifest schema file not found" in str(excinfo.value)

    @patch('devsynth.application.cli.ingest_cmd.sys.path.append')
    @patch('devsynth.application.cli.ingest_cmd.Path')
    def test_validate_manifest_validation_failed(self, mock_path, mock_append):
        """Test validate_manifest with a validation failure."""
        # Set up mocks
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True
        mock_manifest_path.parent = "project_root"
        
        mock_schema_path = MagicMock()
        mock_schema_path.exists.return_value = True
        
        mock_path.return_value.parent.parent.parent.parent.parent.__truediv__.return_value = "scripts_dir"
        mock_path.return_value.__truediv__.return_value = mock_schema_path
        
        # Mock the imported validate_manifest function
        mock_validate_manifest_script = MagicMock(return_value=False)
        
        # Mock the import
        with patch.dict('sys.modules', {'validate_manifest': MagicMock(validate_manifest=mock_validate_manifest_script)}):
            # Call the function and verify it raises an error
            with pytest.raises(ManifestError) as excinfo:
                validate_manifest(mock_manifest_path)
            
            assert "Manifest validation failed" in str(excinfo.value)


class TestLoadManifest:
    """Tests for the load_manifest function."""

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_manifest_success(self, mock_yaml_load, mock_open):
        """Test load_manifest with a valid manifest."""
        # Set up mocks
        mock_yaml_load.return_value = {"projectName": "TestProject", "version": "0.1.0"}
        
        # Call the function
        result = load_manifest(Path("manifest.yaml"))
        
        # Verify the result
        assert result == {"projectName": "TestProject", "version": "0.1.0"}
        
        # Verify open was called
        mock_open.assert_called_once_with(Path("manifest.yaml"), "r")
        
        # Verify yaml.safe_load was called
        mock_yaml_load.assert_called_once()

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_manifest_yaml_error(self, mock_yaml_load, mock_open):
        """Test load_manifest with a YAML parsing error."""
        # Set up mocks
        mock_yaml_load.side_effect = yaml.YAMLError("Test YAML error")
        
        # Call the function and verify it raises an error
        with pytest.raises(ManifestError) as excinfo:
            load_manifest(Path("manifest.yaml"))
        
        assert "Failed to parse manifest YAML" in str(excinfo.value)

    @patch('builtins.open')
    def test_load_manifest_file_error(self, mock_open):
        """Test load_manifest with a file opening error."""
        # Set up mocks
        mock_open.side_effect = FileNotFoundError("Test file error")
        
        # Call the function and verify it raises an error
        with pytest.raises(ManifestError) as excinfo:
            load_manifest(Path("manifest.yaml"))
        
        assert "Failed to load manifest" in str(excinfo.value)


class TestPhases:
    """Tests for the phase functions."""

    def test_expand_phase(self, mock_console):
        """Test expand_phase function."""
        # Call the function
        result = expand_phase({"projectName": "TestProject"}, verbose=True)
        
        # Verify the result
        assert "artifacts_discovered" in result
        assert "files_processed" in result
        assert "duration_seconds" in result
        
        # Verify console output
        assert mock_console.print.call_count >= 4  # At least 4 print calls

    def test_differentiate_phase(self, mock_console):
        """Test differentiate_phase function."""
        # Call the function
        result = differentiate_phase(
            {"projectName": "TestProject"},
            {"artifacts_discovered": 150},
            verbose=True
        )
        
        # Verify the result
        assert "inconsistencies_found" in result
        assert "gaps_identified" in result
        assert "duration_seconds" in result
        
        # Verify console output
        assert mock_console.print.call_count >= 4  # At least 4 print calls

    def test_refine_phase(self, mock_console):
        """Test refine_phase function."""
        # Call the function
        result = refine_phase(
            {"projectName": "TestProject"},
            {"inconsistencies_found": 10},
            verbose=True
        )
        
        # Verify the result
        assert "relationships_created" in result
        assert "outdated_items_archived" in result
        assert "duration_seconds" in result
        
        # Verify console output
        assert mock_console.print.call_count >= 4  # At least 4 print calls

    def test_retrospect_phase(self, mock_console):
        """Test retrospect_phase function."""
        # Call the function
        result = retrospect_phase(
            {"projectName": "TestProject"},
            {"relationships_created": 75},
            verbose=True
        )
        
        # Verify the result
        assert "insights_captured" in result
        assert "improvements_identified" in result
        assert "duration_seconds" in result
        
        # Verify console output
        assert mock_console.print.call_count >= 4  # At least 4 print calls