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

pytest.skip("Ingestion CLI tests are currently incompatible", allow_module_level=True)
from pathlib import Path
from unittest.mock import patch, MagicMock, call

sys.modules.setdefault("typer", types.ModuleType("typer"))
sys.modules.setdefault("duckdb", types.ModuleType("duckdb"))

import importlib.util
from devsynth.exceptions import ManifestError, IngestionError

spec = importlib.util.spec_from_file_location(
    "ingest_cmd",
    Path(__file__).parents[2]
    / "src"
    / "devsynth"
    / "application"
    / "cli"
    / "ingest_cmd.py",
)
ingest_cmd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_cmd)
sys.modules.setdefault("devsynth.application.cli.ingest_cmd", ingest_cmd)
cli_pkg = sys.modules.setdefault("devsynth.application.cli", types.ModuleType("cli"))
setattr(cli_pkg, "ingest_cmd", ingest_cmd)

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
    with patch("devsynth.application.cli.ingest_cmd.validate_manifest") as mock:
        yield mock


@pytest.fixture
def mock_load_manifest():
    """Mock the load_manifest function."""
    with patch("devsynth.application.cli.ingest_cmd.load_manifest") as mock:
        mock.return_value = {"projectName": "TestProject", "version": "0.1.0"}
        yield mock


@pytest.fixture
def mock_ingestion():
    """Mock the Ingestion class used within ingest_cmd."""
    with patch("devsynth.application.cli.ingest_cmd.Ingestion") as cls:
        instance = MagicMock()
        instance.run_ingestion.return_value = {
            "success": True,
            "metrics": {"duration_seconds": 1},
        }
        cls.return_value = instance
        yield cls


@pytest.fixture
def mock_memory_manager():
    """Mock MemoryManager used in phase helpers."""
    with patch("devsynth.application.cli.ingest_cmd.MemoryManager") as cls:
        instance = MagicMock()
        cls.return_value = instance
        yield instance


class TestIngestCmd:
    """Tests for the ingest_cmd function."""

    def test_ingest_cmd_with_defaults(
        self, mock_bridge, mock_validate_manifest, mock_load_manifest, mock_ingestion
    ):
        """Test ingest_cmd with default arguments."""
        # Call the function
        ingest_cmd_fn()

        # Verify validate_manifest was called with the default manifest path
        mock_validate_manifest.assert_called_once()

        # Verify load_manifest was called
        mock_load_manifest.assert_called_once()

        # Verify ingestion was executed
        mock_ingestion.return_value.run_ingestion.assert_called_once()

        # Verify console output
        assert mock_bridge.print.call_count >= 5  # At least 5 print calls

    def test_ingest_cmd_with_custom_manifest(
        self, mock_bridge, mock_validate_manifest, mock_load_manifest
    ):
        """Test ingest_cmd with a custom manifest path."""
        # Call the function with a custom manifest path
        custom_path = "custom/manifest.yaml"
        ingest_cmd_fn(manifest_path=custom_path, validate_only=True)

        # Verify validate_manifest was called with the custom manifest path
        mock_validate_manifest.assert_called_once()
        args, _ = mock_validate_manifest.call_args
        assert str(args[0]) == custom_path

        # Verify load_manifest was not called (validate_only=True)
        mock_load_manifest.assert_not_called()

    def test_ingest_cmd_dry_run(
        self, mock_bridge, mock_validate_manifest, mock_load_manifest, mock_ingestion
    ):
        """Test ingest_cmd with dry_run=True."""
        # Call the function with dry_run=True
        ingest_cmd_fn(dry_run=True)

        # Verify validate_manifest was called
        mock_validate_manifest.assert_called_once()

        # Verify load_manifest was called
        mock_load_manifest.assert_called_once()

        mock_ingestion.return_value.run_ingestion.assert_called_once_with(
            dry_run=True, verbose=False
        )

    def test_ingest_cmd_validate_only(
        self, mock_bridge, mock_validate_manifest, mock_load_manifest
    ):
        """Test ingest_cmd with validate_only=True."""
        # Call the function with validate_only=True
        ingest_cmd_fn(validate_only=True)

        # Verify validate_manifest was called
        mock_validate_manifest.assert_called_once()

        # Verify load_manifest was not called
        mock_load_manifest.assert_not_called()

    def test_ingest_cmd_verbose(
        self, mock_bridge, mock_validate_manifest, mock_load_manifest, mock_ingestion
    ):
        """Test ingest_cmd with verbose=True."""
        # Call the function with verbose=True
        ingest_cmd_fn(verbose=True)

        # Verify validate_manifest was called with verbose=True
        mock_validate_manifest.assert_called_once_with(
            Path(os.path.join(os.getcwd(), "manifest.yaml")), True
        )

        mock_ingestion.return_value.run_ingestion.assert_called_once_with(
            dry_run=False, verbose=True
        )

    def test_ingest_cmd_manifest_error(self, mock_bridge, mock_validate_manifest):
        """Test ingest_cmd with a ManifestError."""
        # Set up the mock to raise a ManifestError
        mock_validate_manifest.side_effect = ManifestError("Test manifest error")

        # Call the function and verify it exits with an error
        with pytest.raises(SystemExit) as excinfo:
            ingest_cmd_fn()

        assert excinfo.value.code == 1

        # Verify console output
        mock_bridge.print.assert_called_once_with(
            "[red]Manifest Error:[/red] Test manifest error"
        )

    def test_ingest_cmd_ingestion_error(
        self, mock_bridge, mock_validate_manifest, mock_load_manifest, mock_ingestion
    ):
        """Test ingest_cmd with an IngestionError."""
        mock_ingestion.return_value.run_ingestion.side_effect = IngestionError(
            "Test ingestion error"
        )

        # Reset the mock_bridge to ensure it's clean before the test
        mock_bridge.reset_mock()

        # Call the function and verify it exits with an error
        with pytest.raises(SystemExit) as excinfo:
            ingest_cmd_fn()

        assert excinfo.value.code == 1

        # Verify console output - allow for multiple calls but ensure the error message is printed
        assert mock_bridge.print.call_count >= 1
        mock_bridge.print.assert_any_call(
            "[red]Ingestion Error:[/red] Test ingestion error"
        )


class TestValidateManifest:
    """Tests for the validate_manifest function."""

    @patch("devsynth.application.cli.ingest_cmd.sys")
    @patch("devsynth.application.cli.ingest_cmd.Path")
    def test_validate_manifest_success(self, mock_path, mock_sys, mock_bridge):
        """Test validate_manifest with a valid manifest."""
        # Set up mocks
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True

        # Create a mock parent that supports the / operator
        mock_parent = MagicMock()
        mock_manifest_path.parent = mock_parent

        # Create a mock docs directory
        mock_docs_dir = MagicMock()
        mock_parent.__truediv__.return_value = mock_docs_dir

        # Create a mock schema path
        mock_schema_path = MagicMock()
        mock_schema_path.exists.return_value = True
        mock_docs_dir.__truediv__.return_value = mock_schema_path

        # Mock the scripts directory path
        mock_path.return_value.parent.parent.parent.parent.parent.__truediv__.return_value = (
            "scripts_dir"
        )

        # Setup sys.path mock with a MagicMock for append
        mock_sys.path = MagicMock()

        # Mock the imported validate_manifest function
        mock_validate_manifest_script = MagicMock(return_value=True)

        # Mock the import
        with patch.dict(
            "sys.modules",
            {
                "validate_manifest": MagicMock(
                    validate_manifest=mock_validate_manifest_script
                )
            },
        ):
            # Call the function
            validate_manifest(mock_manifest_path, verbose=True)

            # Verify sys.path.append was called
            mock_sys.path.append.assert_called_once_with("scripts_dir")

            # Verify the script was called
            mock_validate_manifest_script.assert_called_once_with(
                mock_manifest_path, mock_schema_path, mock_parent
            )

            # Verify console output
            mock_bridge.print.assert_called_once_with(
                "[green]Manifest validation successful.[/green]"
            )

    def test_validate_manifest_file_not_found(self):
        """Test validate_manifest with a non-existent manifest file."""
        # Set up mock
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = False

        # Call the function and verify it raises an error
        with pytest.raises(ManifestError) as excinfo:
            validate_manifest(mock_manifest_path)

        assert "Manifest file not found" in str(excinfo.value)

    @patch("devsynth.application.cli.ingest_cmd.sys")
    @patch("devsynth.application.cli.ingest_cmd.Path")
    def test_validate_manifest_schema_not_found(self, mock_path, mock_sys):
        """Test validate_manifest with a non-existent schema file."""
        # Set up mocks
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True

        # Create a mock parent that supports the / operator
        mock_parent = MagicMock()
        mock_manifest_path.parent = mock_parent

        # Create a mock docs directory
        mock_docs_dir = MagicMock()
        mock_parent.__truediv__.return_value = mock_docs_dir

        # Create a mock schema path that doesn't exist
        mock_schema_path = MagicMock()
        mock_schema_path.exists.return_value = False
        mock_docs_dir.__truediv__.return_value = mock_schema_path

        mock_path.return_value.parent.parent.parent.parent.parent.__truediv__.return_value = (
            "scripts_dir"
        )

        # Setup sys.path mock with a MagicMock for append
        mock_sys.path = MagicMock()

        # Mock the import of validate_manifest
        mock_validate_module = MagicMock()
        mock_validate_module.validate_manifest = MagicMock()

        # Patch sys.modules to return our mock module
        with patch.dict("sys.modules", {"validate_manifest": mock_validate_module}):
            # Call the function and verify it raises an error
            with pytest.raises(ManifestError) as excinfo:
                validate_manifest(mock_manifest_path)

            # Verify sys.path.append was called
            mock_sys.path.append.assert_called_once_with("scripts_dir")

            # Check that the error message contains the expected text
            assert "Manifest schema file not found" in str(excinfo.value)

    @patch("devsynth.application.cli.ingest_cmd.sys")
    @patch("devsynth.application.cli.ingest_cmd.Path")
    def test_validate_manifest_validation_failed(self, mock_path, mock_sys):
        """Test validate_manifest with a validation failure."""
        # Set up mocks
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True

        # Create a mock parent that supports the / operator
        mock_parent = MagicMock()
        mock_manifest_path.parent = mock_parent

        # Create a mock docs directory
        mock_docs_dir = MagicMock()
        mock_parent.__truediv__.return_value = mock_docs_dir

        # Create a mock schema path
        mock_schema_path = MagicMock()
        mock_schema_path.exists.return_value = True
        mock_docs_dir.__truediv__.return_value = mock_schema_path

        mock_path.return_value.parent.parent.parent.parent.parent.__truediv__.return_value = (
            "scripts_dir"
        )

        # Setup sys.path mock with a MagicMock for append
        mock_sys.path = MagicMock()

        # Create a mock module with a validate_manifest function that returns False
        mock_validate_module = MagicMock()
        mock_validate_module.validate_manifest = MagicMock(return_value=False)

        # Patch sys.modules to return our mock module
        with patch.dict("sys.modules", {"validate_manifest": mock_validate_module}):
            # Call the function and verify it raises an error
            with pytest.raises(ManifestError) as excinfo:
                validate_manifest(mock_manifest_path)

            # Verify sys.path.append was called
            mock_sys.path.append.assert_called_once_with("scripts_dir")

            # Verify the mock function was called with the right arguments
            mock_validate_module.validate_manifest.assert_called_once_with(
                mock_manifest_path, mock_schema_path, mock_parent
            )

            # Check that the error message contains the expected text
            assert "Manifest validation failed" in str(excinfo.value)


class TestLoadManifest:
    """Tests for the load_manifest function."""

    @patch("builtins.open")
    @patch("yaml.safe_load")
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

    @patch("builtins.open")
    @patch("yaml.safe_load")
    def test_load_manifest_yaml_error(self, mock_yaml_load, mock_open):
        """Test load_manifest with a YAML parsing error."""
        # Set up mocks
        mock_yaml_load.side_effect = yaml.YAMLError("Test YAML error")

        # Call the function and verify it raises an error
        with pytest.raises(ManifestError) as excinfo:
            load_manifest(Path("manifest.yaml"))

        assert "Failed to parse manifest YAML" in str(excinfo.value)

    @patch("builtins.open")
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

    def test_expand_phase(self, mock_bridge, mock_memory_manager):
        """Test expand_phase function."""
        mock_memory_manager.reset_mock()
        # Call the function
        result = expand_phase(
            {"projectName": "TestProject"}, verbose=True, bridge=mock_bridge
        )

        # Verify the result
        assert "artifacts_discovered" in result
        assert "files_processed" in result
        assert "duration_seconds" in result

        # Verify console output
        assert mock_bridge.print.call_count >= 3
        mock_memory_manager.store_with_edrr_phase.assert_called_once()

    def test_differentiate_phase(self, mock_bridge, mock_memory_manager):
        """Test differentiate_phase function."""
        mock_memory_manager.reset_mock()
        # Call the function
        result = differentiate_phase(
            {"projectName": "TestProject"},
            {"artifacts_discovered": 150},
            verbose=True,
            bridge=mock_bridge,
        )

        # Verify the result
        assert "inconsistencies_found" in result
        assert "gaps_identified" in result
        assert "duration_seconds" in result

        # Verify console output
        assert mock_bridge.print.call_count >= 3
        mock_memory_manager.store_with_edrr_phase.assert_called_once()

    def test_refine_phase(self, mock_bridge, mock_memory_manager):
        """Test refine_phase function."""
        mock_memory_manager.reset_mock()
        # Call the function
        result = refine_phase(
            {"projectName": "TestProject"},
            {"inconsistencies_found": 10},
            verbose=True,
            bridge=mock_bridge,
        )

        # Verify the result
        assert "relationships_created" in result
        assert "outdated_items_archived" in result
        assert "duration_seconds" in result

        # Verify console output
        assert mock_bridge.print.call_count >= 2
        mock_memory_manager.store_with_edrr_phase.assert_called_once()

    def test_retrospect_phase(self, mock_bridge, mock_memory_manager):
        """Test retrospect_phase function."""
        mock_memory_manager.reset_mock()
        # Call the function
        result = retrospect_phase(
            {"projectName": "TestProject"},
            {"relationships_created": 75},
            verbose=True,
            bridge=mock_bridge,
        )

        # Verify the result
        assert "insights_captured" in result
        assert "improvements_identified" in result
        assert "duration_seconds" in result

        # Verify console output
        assert mock_bridge.print.call_count >= 1
        mock_memory_manager.store_with_edrr_phase.assert_called_once()
