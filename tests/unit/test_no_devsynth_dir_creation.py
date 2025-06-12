"""
Unit Tests for Preventing .devsynth Directory Creation

This file contains unit tests to verify that .devsynth directories are not
created during test runs when file operations are disabled.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

from devsynth.config.settings import get_settings, ensure_path_exists


class TestNoDevSynthDirCreation:
    """Tests for ensuring .devsynth directories are not created when file operations are disabled."""

    def test_ensure_path_exists_respects_no_file_logging(self, monkeypatch):
        """
        Test that ensure_path_exists respects the DEVSYNTH_NO_FILE_LOGGING environment variable.
        
        This test verifies that when DEVSYNTH_NO_FILE_LOGGING is set to "1", the
        ensure_path_exists function does not create directories.
        """
        # Set up a test path
        test_path = Path(os.getcwd()) / "test_dir_that_should_not_be_created"
        
        try:
            # Ensure file logging is disabled
            monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
            
            # Call ensure_path_exists with create=True
            ensure_path_exists(str(test_path), create=True)
            
            # Verify that the directory was not created
            assert not test_path.exists(), f"Directory was created despite file logging being disabled: {test_path}"
            
            # Now test with file logging enabled
            monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")
            
            # Call ensure_path_exists with create=True
            ensure_path_exists(str(test_path), create=True)
            
            # Verify that the directory was created
            assert test_path.exists(), f"Directory was not created when file logging is enabled: {test_path}"
            
        finally:
            # Clean up the test directory if it was created
            if test_path.exists():
                test_path.rmdir()

    def test_settings_respects_no_file_logging(self, monkeypatch, tmp_path):
        """
        Test that settings respects the DEVSYNTH_NO_FILE_LOGGING environment variable.
        
        This test verifies that when DEVSYNTH_NO_FILE_LOGGING is set to "1", the
        settings do not use home directory paths for memory and logs.
        """
        # Set up a test project directory
        test_project_dir = tmp_path / "test_project"
        test_project_dir.mkdir()
        
        # Set environment variables
        monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
        monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(test_project_dir))
        
        # Get settings
        settings = get_settings(reload=True)
        
        # Verify that memory_file_path is not in the home directory
        assert "~/.devsynth" not in settings.memory_file_path, f"Memory path uses home directory: {settings.memory_file_path}"
        assert str(test_project_dir) in settings.memory_file_path, f"Memory path does not use project directory: {settings.memory_file_path}"
        
        # Verify that log_dir is not in the home directory
        assert "~/.devsynth" not in settings.log_dir, f"Log directory uses home directory: {settings.log_dir}"
        assert str(test_project_dir) in settings.log_dir, f"Log directory does not use project directory: {settings.log_dir}"
        
        # Verify that the directories were not created
        memory_path = Path(settings.memory_file_path)
        log_path = Path(settings.log_dir)
        
        assert not memory_path.exists(), f"Memory directory was created despite file logging being disabled: {memory_path}"
        assert not log_path.exists(), f"Log directory was created despite file logging being disabled: {log_path}"
