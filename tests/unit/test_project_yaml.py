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
    """Tests for loading the project configuration file from the new location.

ReqID: N/A"""

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_project_yaml_success_succeeds(self, mock_yaml_load, mock_open
        ):
        """Test loading the project configuration file from .devsynth/project.yaml.

ReqID: N/A"""
        mock_yaml_load.return_value = {'projectName': 'TestProject',
            'version': '0.1.0'}
        result = load_manifest(Path('.devsynth/project.yaml'))
        assert result == {'projectName': 'TestProject', 'version': '0.1.0'}
        mock_open.assert_called_once_with(Path('.devsynth/project.yaml'), 'r')
        mock_yaml_load.assert_called_once()

    @patch('builtins.open')
    @patch('yaml.safe_load')
    @patch('os.path.exists')
    def test_load_project_yaml_fallback_to_legacy_succeeds(self,
        mock_exists, mock_yaml_load, mock_open):
        """Test fallback to legacy manifest.yaml if .devsynth/project.yaml doesn't exist.

ReqID: N/A"""
        mock_exists.side_effect = lambda path: str(path
            ) != '.devsynth/project.yaml'
        mock_file = MagicMock()
        mock_open.return_value = mock_file
        mock_yaml_load.return_value = {'projectName': 'TestProject',
            'version': '0.1.0'}
        result = load_manifest(None)
        assert result == {'projectName': 'TestProject', 'version': '0.1.0'}
        mock_open.assert_called_once_with(Path('manifest.yaml'), 'r')
        mock_yaml_load.assert_called_once()

    @patch('os.path.exists')
    def test_project_yaml_path_preference_succeeds(self, mock_exists):
        """Test that .devsynth/project.yaml is preferred over manifest.yaml when both exist.

ReqID: N/A"""
        mock_exists.return_value = True
        with patch('builtins.open', MagicMock()) as mock_open:
            with patch('yaml.safe_load', return_value={'projectName':
                'TestProject'}) as mock_yaml_load:
                result = load_manifest(None)
                mock_open.assert_called_once_with(Path(
                    '.devsynth/project.yaml'), 'r')

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_manifest_version_locking_succeeds(self, mock_yaml_load, mock_open
        ):
        """Version field is preserved when loading project.yaml.

ReqID: N/A"""
        mock_yaml_load.return_value = {'metadata': {'version': '9.9.9'}}
        result = load_manifest(Path('.devsynth/project.yaml'))
        assert result['metadata']['version'] == '9.9.9'
        mock_open.assert_called_once_with(Path('.devsynth/project.yaml'), 'r')
        mock_yaml_load.assert_called_once()

    @patch('os.path.exists')
    def test_default_manifest_returned_when_missing_returns_expected_result(
        self, mock_exists):
        """load_manifest returns minimal default manifest when no file is present.

ReqID: N/A"""
        mock_exists.return_value = False
        manifest = load_manifest(None)
        assert manifest['metadata']['name'] == 'Unmanaged Project'
        assert manifest['metadata']['version'] == '0.1.0'
        assert manifest['structure']['type'] == 'standard'
