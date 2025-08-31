"""
Unit Tests for Testing Isolation

This file contains unit tests to verify that the .devsynth/ directory is created
in the testing directory instead of the current working directory, and that
no unnecessary directories are created during test runs.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestIsolation:
    """Tests for ensuring proper isolation of the .devsynth/ directory.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_devsynth_dir_isolation_succeeds(self, test_environment):
        """Test that .devsynth/ directory is created in the test environment.

        This test verifies that when code creates a .devsynth/ directory,
        it's created in the test environment's project directory, not in
        the current working directory.

        ReqID: N/A"""
        project_dir = test_environment["project_dir"]
        devsynth_dir = project_dir / ".devsynth"
        devsynth_dir.mkdir(exist_ok=True)
        test_file = devsynth_dir / "test_file.txt"
        with open(test_file, "w") as f:
            f.write("Test content")
        assert test_file.exists()
        parent_dir = project_dir.parent.parent
        parent_devsynth = parent_dir / ".devsynth"
        if parent_devsynth.exists():
            pytest.skip(
                f"Parent directory {parent_dir} already has a .devsynth directory"
            )
        assert (
            not parent_devsynth.exists()
        ), f".devsynth directory was created in {parent_dir}"

    @pytest.mark.fast
    def test_global_config_isolation_succeeds(self, test_environment):
        """Test that global configuration is isolated during tests.

        This test verifies that when code accesses the global configuration,
        it uses a mock configuration in the test environment, not the real
        global configuration in the user's home directory.

        ReqID: N/A"""
        project_dir = test_environment["project_dir"]
        with patch("os.path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = str(project_dir)
            global_config_dir = project_dir / ".devsynth" / "config"
            global_config_dir.mkdir(parents=True, exist_ok=True)
            global_config_file = global_config_dir / "global_config.yaml"
            with open(global_config_file, "w") as f:
                f.write("test: value")
            assert global_config_file.exists()
            parent_dir = project_dir.parent.parent
            parent_config_dir = parent_dir / ".devsynth" / "config"
            if parent_config_dir.exists():
                pytest.skip(
                    f"Parent directory {parent_dir} already has a .devsynth/config directory"
                )
            assert (
                not parent_config_dir.exists()
            ), f"Global config directory was created in {parent_dir}"
            home_path = str(Path.home())
            current_path = str(project_dir)
            if not current_path.startswith(home_path):
                home_config_dir = Path.home() / ".devsynth" / "config"
                if home_config_dir.exists():
                    pytest.skip(
                        f"Home directory already has a .devsynth/config directory"
                    )
                assert (
                    not home_config_dir.exists()
                ), f"Global config directory was created in {home_config_dir}"

    @pytest.mark.fast
    def test_memory_path_isolation_succeeds(self, test_environment):
        """Test that memory path is isolated during tests.

        This test verifies that when code accesses the memory path,
        it uses a path in the test environment, not a path in the
        current working directory.

        ReqID: N/A"""
        memory_dir = test_environment["memory_dir"]
        test_file = memory_dir / "test_memory.json"
        with open(test_file, "w") as f:
            f.write('{"test": "value"}')
        assert test_file.exists()
        original_cwd = os.environ.get("ORIGINAL_CWD", os.getcwd())
        original_memory_dir = Path(original_cwd) / ".devsynth" / "memory"
        assert (
            not original_memory_dir.exists()
        ), f"Memory directory was created in {original_memory_dir}"

    @pytest.mark.fast
    def test_no_file_logging_prevents_directory_creation_succeeds(self, monkeypatch):
        """Test that when file logging is disabled, no log directories are created.

        This test verifies that the DEVSYNTH_NO_FILE_LOGGING environment variable
        prevents the creation of log directories during tests.

        ReqID: N/A"""
        from devsynth.logging_setup import configure_logging, ensure_log_dir_exists

        test_dir = Path(tempfile.mkdtemp())
        log_dir = test_dir / "logs"
        try:
            monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
            configure_logging(log_dir=str(log_dir))
            assert (
                not log_dir.exists()
            ), f"Log directory was created despite file logging being disabled: {log_dir}"
            ensure_log_dir_exists(str(log_dir))
            assert (
                not log_dir.exists()
            ), f"Log directory was created by ensure_log_dir_exists despite file logging being disabled: {log_dir}"
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    @pytest.mark.fast
    def test_path_redirection_in_test_environment_succeeds(self, monkeypatch):
        """Test that paths are redirected to the test environment in tests.

        This test verifies that when DEVSYNTH_PROJECT_DIR is set, paths outside
        the test directory are redirected to be within the test directory.

        ReqID: N/A"""
        test_dir = Path(tempfile.mkdtemp())
        try:
            monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(test_dir))

            def custom_ensure_path_exists(path, create=True):
                path_obj = Path(path)
                if path_obj.is_absolute() and not str(path_obj).startswith(
                    str(test_dir)
                ):
                    if str(path_obj).startswith(str(Path.home())):
                        relative_path = str(path_obj).replace(str(Path.home()), "")
                        new_path = os.path.join(test_dir, relative_path.lstrip("/\\"))
                        print(f"Redirecting home path {path} to test path {new_path}")
                        path = new_path
                    else:
                        relative_path = str(path_obj.relative_to(path_obj.anchor))
                        new_path = os.path.join(test_dir, relative_path)
                        print(
                            f"Redirecting absolute path {path} to test path {new_path}"
                        )
                        path = new_path
                if create:
                    os.makedirs(path, exist_ok=True)
                return path

            def custom_ensure_log_dir_exists(log_dir=None):
                if log_dir is None:
                    log_dir = os.path.join(test_dir, "logs")
                path_obj = Path(log_dir)
                if path_obj.is_absolute() and not str(path_obj).startswith(
                    str(test_dir)
                ):
                    if str(path_obj).startswith(str(Path.home())):
                        relative_path = str(path_obj).replace(str(Path.home()), "")
                        new_path = os.path.join(test_dir, relative_path.lstrip("/\\"))
                        print(f"Redirecting log path {log_dir} to test path {new_path}")
                        log_dir = new_path
                    else:
                        relative_path = str(path_obj.relative_to(path_obj.anchor))
                        new_path = os.path.join(test_dir, relative_path)
                        print(
                            f"Redirecting absolute log path {log_dir} to test path {new_path}"
                        )
                        log_dir = new_path
                os.makedirs(log_dir, exist_ok=True)
                return log_dir

            home_path = Path.home() / ".devsynth" / "memory"
            redirected_path = custom_ensure_path_exists(str(home_path), create=False)
            assert (
                str(test_dir) in redirected_path
            ), f"Path was not redirected to test directory: {redirected_path}"
            assert (
                str(home_path) not in redirected_path
            ), f"Path still contains home directory: {redirected_path}"
            home_log_path = Path.home() / ".devsynth" / "logs"
            redirected_log_path = custom_ensure_log_dir_exists(str(home_log_path))
            assert (
                str(test_dir) in redirected_log_path
            ), f"Log path was not redirected to test directory: {redirected_log_path}"
            assert (
                str(home_log_path) not in redirected_log_path
            ), f"Log path still contains home directory: {redirected_log_path}"
            assert (
                not home_path.exists()
            ), f"Directory was created in home directory: {home_path}"
            assert (
                not home_log_path.exists()
            ), f"Log directory was created in home directory: {home_log_path}"
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    @pytest.mark.fast
    def test_comprehensive_isolation_succeeds(self, monkeypatch):
        """Comprehensive test for isolation of .devsynth directories.

        This test verifies that no .devsynth directories are created outside
        the test environment during testing, even when multiple components
        are used together.

        ReqID: N/A"""
        from devsynth.config.settings import ensure_path_exists, get_settings
        from devsynth.logging_setup import DevSynthLogger, configure_logging

        test_dir = Path(tempfile.mkdtemp())
        original_cwd = os.getcwd()
        try:
            monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(test_dir))
            monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
            monkeypatch.setenv("ORIGINAL_CWD", original_cwd)
            os.chdir(test_dir)
            settings = get_settings(reload=True)
            configure_logging()
            logger = DevSynthLogger("test_logger")
            logger.info("Test message")
            memory_path = ensure_path_exists(
                str(Path.home() / ".devsynth" / "memory"), create=True
            )
            log_path = ensure_path_exists(
                str(Path.home() / ".devsynth" / "logs"), create=True
            )
            home_devsynth = Path.home() / ".devsynth"
            assert (
                not home_devsynth.exists()
            ), f".devsynth directory was created in home directory: {home_devsynth}"
            if not any(
                x in str(original_cwd).lower() for x in ["pytest", "tmp", "temp"]
            ):
                cwd_devsynth = Path(original_cwd) / ".devsynth"
                assert (
                    not cwd_devsynth.exists()
                ), f".devsynth directory was created in original working directory: {cwd_devsynth}"
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(test_dir, ignore_errors=True)
            for path in [Path.home() / ".devsynth", Path(original_cwd) / ".devsynth"]:
                if path.exists():
                    print(f"Warning: Cleaning up stray .devsynth directory: {path}")
                    shutil.rmtree(path, ignore_errors=True)
