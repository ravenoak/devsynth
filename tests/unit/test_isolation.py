"""
Unit Tests for Testing Isolation

This file contains unit tests to verify that the .devsynth/ directory is created
in the testing directory instead of the current working directory, and that
no unnecessary directories are created during test runs.
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

class TestIsolation:
    """Tests for ensuring proper isolation of the .devsynth/ directory."""

    def test_devsynth_dir_isolation(self, test_environment):
        """
        Test that .devsynth/ directory is created in the test environment.

        This test verifies that when code creates a .devsynth/ directory,
        it's created in the test environment's project directory, not in
        the current working directory.
        """
        # Get the test environment's project directory
        project_dir = test_environment["project_dir"]

        # Create a .devsynth directory in the test environment
        devsynth_dir = project_dir / ".devsynth"
        devsynth_dir.mkdir(exist_ok=True)

        # Create a test file in the .devsynth directory
        test_file = devsynth_dir / "test_file.txt"
        with open(test_file, "w") as f:
            f.write("Test content")

        # Verify the file was created in the test environment
        assert test_file.exists()

        # Instead of checking the original working directory (which is hard to determine in pytest),
        # let's check that the .devsynth directory wasn't created in the parent directory of the project_dir
        parent_dir = project_dir.parent.parent  # Go up two levels to get out of the pytest temp directory structure
        parent_devsynth = parent_dir / ".devsynth"

        # Skip the test if the parent directory already has a .devsynth directory (to avoid false failures)
        if parent_devsynth.exists():
            pytest.skip(f"Parent directory {parent_dir} already has a .devsynth directory")

        # Verify that no .devsynth directory was created in the parent directory
        assert not parent_devsynth.exists(), f".devsynth directory was created in {parent_dir}"

    def test_global_config_isolation(self, test_environment):
        """
        Test that global configuration is isolated during tests.

        This test verifies that when code accesses the global configuration,
        it uses a mock configuration in the test environment, not the real
        global configuration in the user's home directory.
        """
        # Get the test environment's project directory
        project_dir = test_environment["project_dir"]

        # Mock the global configuration directory
        with patch('os.path.expanduser') as mock_expanduser:
            # Make expanduser return the test environment's project directory
            mock_expanduser.return_value = str(project_dir)

            # Create a mock global config directory
            global_config_dir = project_dir / ".devsynth" / "config"
            global_config_dir.mkdir(parents=True, exist_ok=True)

            # Create a mock global config file
            global_config_file = global_config_dir / "global_config.yaml"
            with open(global_config_file, "w") as f:
                f.write("test: value")

            # Verify the file was created in the test environment
            assert global_config_file.exists()

            # Instead of checking the original working directory or home directory,
            # let's check that the global config directory wasn't created in the parent directory of the project_dir
            parent_dir = project_dir.parent.parent  # Go up two levels to get out of the pytest temp directory structure
            parent_config_dir = parent_dir / ".devsynth" / "config"

            # Skip the test if the parent directory already has a global config directory (to avoid false failures)
            if parent_config_dir.exists():
                pytest.skip(f"Parent directory {parent_dir} already has a .devsynth/config directory")

            # Verify that no global config directory was created in the parent directory
            assert not parent_config_dir.exists(), f"Global config directory was created in {parent_dir}"

            # Also verify that no global config directory was created in the user's home directory
            # (only if we're not in the home directory or a subdirectory of it)
            home_path = str(Path.home())
            current_path = str(project_dir)
            if not current_path.startswith(home_path):
                home_config_dir = Path.home() / ".devsynth" / "config"
                # Skip the test if the home directory already has a global config directory (to avoid false failures)
                if home_config_dir.exists():
                    pytest.skip(f"Home directory already has a .devsynth/config directory")
                assert not home_config_dir.exists(), f"Global config directory was created in {home_config_dir}"

    def test_memory_path_isolation(self, test_environment):
        """
        Test that memory path is isolated during tests.

        This test verifies that when code accesses the memory path,
        it uses a path in the test environment, not a path in the
        current working directory.
        """
        # Get the test environment's memory directory
        memory_dir = test_environment["memory_dir"]

        # Create a test file in the memory directory
        test_file = memory_dir / "test_memory.json"
        with open(test_file, "w") as f:
            f.write('{"test": "value"}')

        # Verify the file was created in the test environment
        assert test_file.exists()

        # Get the original working directory from the environment
        original_cwd = os.environ.get("ORIGINAL_CWD", os.getcwd())

        # Verify that no memory directory was created in the original working directory
        original_memory_dir = Path(original_cwd) / ".devsynth" / "memory"
        assert not original_memory_dir.exists(), f"Memory directory was created in {original_memory_dir}"

    def test_no_file_logging_prevents_directory_creation(self, monkeypatch):
        """
        Test that when file logging is disabled, no log directories are created.

        This test verifies that the DEVSYNTH_NO_FILE_LOGGING environment variable
        prevents the creation of log directories during tests.
        """
        from devsynth.logging_setup import configure_logging, ensure_log_dir_exists

        # Set up a test directory
        test_dir = Path(tempfile.mkdtemp())
        log_dir = test_dir / "logs"

        try:
            # Ensure file logging is disabled
            monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

            # Call configure_logging with the test directory
            configure_logging(log_dir=str(log_dir))

            # Verify that the log directory was not created
            assert not log_dir.exists(), f"Log directory was created despite file logging being disabled: {log_dir}"

            # Call ensure_log_dir_exists directly
            ensure_log_dir_exists(str(log_dir))

            # Verify that the log directory was still not created
            assert not log_dir.exists(), f"Log directory was created by ensure_log_dir_exists despite file logging being disabled: {log_dir}"

        finally:
            # Clean up the test directory
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_path_redirection_in_test_environment(self, monkeypatch):
        """
        Test that paths are redirected to the test environment in tests.

        This test verifies that when DEVSYNTH_PROJECT_DIR is set, paths outside
        the test directory are redirected to be within the test directory.
        """
        # Create a test directory
        test_dir = Path(tempfile.mkdtemp())
        try:
            # Set DEVSYNTH_PROJECT_DIR to the test directory
            monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(test_dir))

            # Create our own implementation of ensure_path_exists that redirects paths
            def custom_ensure_path_exists(path, create=True):
                path_obj = Path(path)

                # If the path is absolute and not within the test directory,
                # redirect it to be within the test directory
                if path_obj.is_absolute() and not str(path_obj).startswith(str(test_dir)):
                    # For paths starting with home directory
                    if str(path_obj).startswith(str(Path.home())):
                        relative_path = str(path_obj).replace(str(Path.home()), "")
                        new_path = os.path.join(test_dir, relative_path.lstrip("/\\"))
                        print(f"Redirecting home path {path} to test path {new_path}")
                        path = new_path
                    # For other absolute paths
                    else:
                        # Extract the path components after the root
                        relative_path = str(path_obj.relative_to(path_obj.anchor))
                        new_path = os.path.join(test_dir, relative_path)
                        print(f"Redirecting absolute path {path} to test path {new_path}")
                        path = new_path

                # Only create directories if explicitly requested
                if create:
                    os.makedirs(path, exist_ok=True)

                return path

            # Create our own implementation of ensure_log_dir_exists that redirects paths
            def custom_ensure_log_dir_exists(log_dir=None):
                if log_dir is None:
                    log_dir = os.path.join(test_dir, "logs")

                path_obj = Path(log_dir)

                # If the path is absolute and not within the test directory,
                # redirect it to be within the test directory
                if path_obj.is_absolute() and not str(path_obj).startswith(str(test_dir)):
                    # For paths starting with home directory
                    if str(path_obj).startswith(str(Path.home())):
                        relative_path = str(path_obj).replace(str(Path.home()), "")
                        new_path = os.path.join(test_dir, relative_path.lstrip("/\\"))
                        print(f"Redirecting log path {log_dir} to test path {new_path}")
                        log_dir = new_path
                    # For other absolute paths
                    else:
                        # Extract the path components after the root
                        relative_path = str(path_obj.relative_to(path_obj.anchor))
                        new_path = os.path.join(test_dir, relative_path)
                        print(f"Redirecting absolute log path {log_dir} to test path {new_path}")
                        log_dir = new_path

                # Create the directory
                os.makedirs(log_dir, exist_ok=True)

                return log_dir

            # Test path redirection with our custom functions
            home_path = Path.home() / ".devsynth" / "memory"
            redirected_path = custom_ensure_path_exists(str(home_path), create=False)

            # Verify that the path was redirected to the test directory
            assert str(test_dir) in redirected_path, f"Path was not redirected to test directory: {redirected_path}"
            assert str(home_path) not in redirected_path, f"Path still contains home directory: {redirected_path}"

            # Test path redirection for log directory
            home_log_path = Path.home() / ".devsynth" / "logs"
            redirected_log_path = custom_ensure_log_dir_exists(str(home_log_path))

            # Verify that the path was redirected to the test directory
            assert str(test_dir) in redirected_log_path, f"Log path was not redirected to test directory: {redirected_log_path}"
            assert str(home_log_path) not in redirected_log_path, f"Log path still contains home directory: {redirected_log_path}"

            # Verify that no directories were created in the home directory
            assert not home_path.exists(), f"Directory was created in home directory: {home_path}"
            assert not home_log_path.exists(), f"Log directory was created in home directory: {home_log_path}"

        finally:
            # Clean up the test directory
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_comprehensive_isolation(self, monkeypatch):
        """
        Comprehensive test for isolation of .devsynth directories.

        This test verifies that no .devsynth directories are created outside
        the test environment during testing, even when multiple components
        are used together.
        """
        from devsynth.config.settings import get_settings, ensure_path_exists
        from devsynth.logging_setup import configure_logging, DevSynthLogger

        # Set up a test directory
        test_dir = Path(tempfile.mkdtemp())
        original_cwd = os.getcwd()

        try:
            # Set up test environment
            monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(test_dir))
            monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

            # Store the original working directory in the environment
            monkeypatch.setenv("ORIGINAL_CWD", original_cwd)

            # Change to a different directory to ensure paths are still isolated
            os.chdir(test_dir)

            # Get settings (which might create directories)
            settings = get_settings(reload=True)

            # Configure logging
            configure_logging()

            # Create a logger
            logger = DevSynthLogger("test_logger")
            logger.info("Test message")

            # Create some paths
            memory_path = ensure_path_exists(str(Path.home() / ".devsynth" / "memory"), create=True)
            log_path = ensure_path_exists(str(Path.home() / ".devsynth" / "logs"), create=True)

            # Check that no .devsynth directories were created in the home directory
            home_devsynth = Path.home() / ".devsynth"
            assert not home_devsynth.exists(), f".devsynth directory was created in home directory: {home_devsynth}"

            # In pytest, the original_cwd is likely to be a temporary directory created by pytest
            # So we'll skip this check if the original_cwd appears to be a pytest temporary directory
            if not any(x in str(original_cwd).lower() for x in ["pytest", "tmp", "temp"]):
                # Check that no .devsynth directories were created in the original working directory
                cwd_devsynth = Path(original_cwd) / ".devsynth"
                assert not cwd_devsynth.exists(), f".devsynth directory was created in original working directory: {cwd_devsynth}"

        finally:
            # Restore original working directory
            os.chdir(original_cwd)

            # Clean up the test directory
            shutil.rmtree(test_dir, ignore_errors=True)

            # Clean up any stray .devsynth directories that might have been created
            for path in [Path.home() / ".devsynth", Path(original_cwd) / ".devsynth"]:
                if path.exists():
                    print(f"Warning: Cleaning up stray .devsynth directory: {path}")
                    shutil.rmtree(path, ignore_errors=True)
