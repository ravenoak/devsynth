"""
Unit Tests for Project YAML Loading

This file contains unit tests for loading the project configuration file
from the new location (.devsynth/project.yaml) instead of the legacy location (manifest.yaml).
"""
import os
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from devsynth.application.cli.ingest_cmd import load_manifest
from devsynth.exceptions import ManifestError

class TestProjectYamlLoading:
    """Tests for loading the project configuration file from the new location."""

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_project_yaml_success(self, mock_yaml_load, mock_open):
        """Test loading the project configuration file from .devsynth/project.yaml."""
        # Set up mocks
        mock_yaml_load.return_value = {"projectName": "TestProject", "version": "0.1.0"}

        # Call the function with the new path
        result = load_manifest(Path(".devsynth/project.yaml"))

        # Verify the result
        assert result == {"projectName": "TestProject", "version": "0.1.0"}

        # Verify open was called with the new path
        mock_open.assert_called_once_with(Path(".devsynth/project.yaml"), "r")

        # Verify yaml.safe_load was called
        mock_yaml_load.assert_called_once()

    @patch('builtins.open')
    @patch('yaml.safe_load')
    @patch('os.path.exists')
    def test_load_project_yaml_fallback_to_legacy(self, mock_exists, mock_yaml_load, mock_open):
        """Test fallback to legacy manifest.yaml if .devsynth/project.yaml doesn't exist."""
        # Set up mock for os.path.exists to return False for new path
        mock_exists.side_effect = lambda path: str(path) != ".devsynth/project.yaml"

        # Set up mocks for open to succeed on the second call (manifest.yaml)
        mock_file = MagicMock()
        mock_open.return_value = mock_file
        mock_yaml_load.return_value = {"projectName": "TestProject", "version": "0.1.0"}

        # Call the function with automatic path detection
        result = load_manifest(None)  # None should trigger automatic path detection

        # Verify the result
        assert result == {"projectName": "TestProject", "version": "0.1.0"}

        # Verify open was called with the legacy path
        mock_open.assert_called_once_with(Path("manifest.yaml"), "r")

        # Verify yaml.safe_load was called
        mock_yaml_load.assert_called_once()

    @patch('os.path.exists')
    def test_project_yaml_path_preference(self, mock_exists):
        """Test that .devsynth/project.yaml is preferred over manifest.yaml when both exist."""
        # Set up mock to indicate both files exist
        mock_exists.return_value = True

        # Mock the open and yaml.safe_load functions
        with patch('builtins.open', MagicMock()) as mock_open:
            with patch('yaml.safe_load', return_value={"projectName": "TestProject"}) as mock_yaml_load:
                # Call the function with automatic path detection
                result = load_manifest(None)  # None should trigger automatic path detection

                # Verify open was called with the new path
                mock_open.assert_called_once_with(Path(".devsynth/project.yaml"), "r")
