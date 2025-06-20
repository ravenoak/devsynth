"""
Configuration for pytest with comprehensive test isolation.

This module provides fixtures for ensuring all tests are hermetic (isolated from side effects)
and don't pollute the developer's environment, file system, or depend on external services.
"""

import os
import sys
import pytest
import tempfile
import shutil
import uuid
import socket
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from devsynth.config.settings import ensure_path_exists


# Add a marker for tests requiring external resources
requires_resource = pytest.mark.requires_resource


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_resource(name): mark test as requiring an external resource",
    )


@pytest.fixture
def test_environment(tmp_path, monkeypatch):
    """
    Create a completely isolated test environment with temporary directories and patched environment variables.
    This fixture is NOT automatically used for all tests - use global_test_isolation instead.

    This fixture provides:
    1. A temporary project directory with a basic .devsynth structure
    2. Temporary directories for logs and memory
    3. Environment variables pointing to these temporary directories

    Args:
        tmp_path (Path): Pytest-provided temporary directory
        monkeypatch: Pytest monkeypatch fixture
    """
    # Create common directories in the temporary path
    project_dir = tmp_path / "project"
    logs_dir = tmp_path / "logs"
    devsynth_dir = project_dir / ".devsynth"
    memory_dir = devsynth_dir / "memory"

    # Create directories
    project_dir.mkdir(exist_ok=True)

    # Only create log directories if file logging is not disabled
    no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
        "1",
        "true",
        "yes",
    )

    if not no_file_logging:
        logs_dir.mkdir(exist_ok=True)

    # Always create the basic .devsynth structure for tests that expect it
    devsynth_dir.mkdir(exist_ok=True)
    memory_dir.mkdir(exist_ok=True)

    # Set up a basic project structure
    with open(devsynth_dir / "config.json", "w") as f:
        f.write('{"model": "test-model", "project_name": "test-project"}')
    # Create devsynth.yml for the config loader
    with open(devsynth_dir / "devsynth.yml", "w") as f:
        f.write("language: python\n")

    # Return the environment information
    return {
        "project_dir": project_dir,
        "logs_dir": logs_dir,
        "memory_dir": memory_dir,
        "devsynth_dir": devsynth_dir,
    }


@pytest.fixture
def tmp_project_dir():
    """
    Create a temporary directory for a DevSynth project.

    This fixture creates a temporary directory with basic DevSynth project structure
    and cleans it up after the test.

    Returns:
        Path: The path to the temporary project directory
    """
    # Create a temporary directory
    temp_dir = Path(tempfile.mkdtemp())

    # Record the start time to identify files created during the test
    start_time = datetime.now()

    # Create basic project structure
    ensure_path_exists(str(temp_dir / ".devsynth"))

    # Create a mock config file
    with open(temp_dir / ".devsynth" / "config.json", "w") as f:
        f.write('{"model": "gpt-4", "project_name": "test-project"}')
    # Also write a devsynth.yml file for the unified loader
    with open(temp_dir / ".devsynth" / "devsynth.yml", "w") as f:
        f.write("language: python\n")

    # Set environment variable to disable file logging
    old_env_value = os.environ.get("DEVSYNTH_NO_FILE_LOGGING")
    os.environ["DEVSYNTH_NO_FILE_LOGGING"] = "1"

    # Return the path to the temporary directory
    yield temp_dir

    # Restore original environment variable value
    if old_env_value is not None:
        os.environ["DEVSYNTH_NO_FILE_LOGGING"] = old_env_value
    else:
        os.environ.pop("DEVSYNTH_NO_FILE_LOGGING", None)

    # Clean up the temporary directory after the test
    try:
        shutil.rmtree(temp_dir)
    except (PermissionError, OSError) as e:
        print(f"Warning: Failed to clean up temporary directory {temp_dir}: {str(e)}")

    # Clean up any stray artifacts in the current working directory
    for artifact in [".devsynth", "logs"]:
        path = Path(os.getcwd()) / artifact
        if path.exists():
            try:
                # Check if directory was created or modified during the test
                dir_stat = path.stat()
                dir_mtime = datetime.fromtimestamp(dir_stat.st_mtime)

                if dir_mtime >= start_time:
                    print(f"Cleaning up test artifact: {path}")
                    shutil.rmtree(path)
            except (PermissionError, OSError) as e:
                print(f"Warning: Failed to clean up {path}: {str(e)}")


@pytest.fixture
def mock_datetime():
    """
    Patch datetime.now() to return a fixed value for reproducible tests.
    """
    fixed_dt = datetime(2025, 1, 1, 12, 0, 0)
    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_dt
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield mock_dt


@pytest.fixture
def mock_uuid():
    """
    Patch uuid.uuid4() to return predictable values for reproducible tests.
    """
    fixed_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    with patch("uuid.uuid4", return_value=fixed_id) as mock_id:
        yield mock_id


@pytest.fixture
def temp_memory_path(tmp_path):
    """
    Create a temporary memory storage path.

    Returns:
        Path: Path to a temporary directory for memory storage
    """
    memory_path = tmp_path / ".devsynth" / "memory"
    ensure_path_exists(str(memory_path.parent))
    return memory_path


@pytest.fixture
def temp_log_dir(tmp_path):
    """
    Create a temporary log directory.

    Returns:
        Path: Path to a temporary directory for logs
    """
    log_path = tmp_path / "logs"
    ensure_path_exists(str(log_path))
    return log_path


@pytest.fixture
def patch_settings_paths(monkeypatch, temp_memory_path, temp_log_dir):
    """
    DEPRECATED: This fixture is no longer needed as its functionality has been incorporated into global_test_isolation.

    This fixture is kept for backward compatibility with existing tests that might depend on it.
    New tests should rely on the global_test_isolation fixture instead.
    """
    # This fixture doesn't do anything anymore as its functionality
    # has been incorporated into global_test_isolation
    yield


@pytest.fixture(autouse=True)
def global_test_isolation(monkeypatch, tmp_path):
    """
    Global fixture to ensure all tests are properly isolated.

    This autoused fixture:
    1. Saves and restores all environment variables
    2. Saves and restores the working directory
    3. Creates a temporary test environment
    4. Patches paths to use temporary directories
    5. Disables file logging for tests
    6. Patches logging configuration
    7. Cleans up any artifacts after tests

    By using autouse=True, this fixture applies to ALL tests.
    """
    # Save original environment
    original_env = dict(os.environ)

    # Save original working directory
    original_cwd = os.getcwd()

    # Store the original working directory in the environment
    os.environ["ORIGINAL_CWD"] = original_cwd

    # Create test environment directories
    test_env = {}
    project_dir = tmp_path / "project"
    logs_dir = tmp_path / "logs"
    devsynth_dir = project_dir / ".devsynth"
    memory_dir = devsynth_dir / "memory"
    config_dir = devsynth_dir / "config"
    checkpoints_dir = devsynth_dir / "checkpoints"
    workflows_dir = devsynth_dir / "workflows"

    # Create directories
    project_dir.mkdir(exist_ok=True)
    devsynth_dir.mkdir(exist_ok=True)
    memory_dir.mkdir(exist_ok=True)
    config_dir.mkdir(exist_ok=True)
    checkpoints_dir.mkdir(exist_ok=True)
    workflows_dir.mkdir(exist_ok=True)

    # Set up a basic project structure
    with open(devsynth_dir / "config.json", "w") as f:
        f.write('{"model": "test-model", "project_name": "test-project"}')

    # Set environment variables to use temporary directories
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    monkeypatch.setenv("DEVSYNTH_LOG_DIR", str(logs_dir))
    monkeypatch.setenv("DEVSYNTH_MEMORY_PATH", str(memory_dir))
    monkeypatch.setenv("DEVSYNTH_CHECKPOINTS_PATH", str(checkpoints_dir))
    monkeypatch.setenv("DEVSYNTH_WORKFLOWS_PATH", str(workflows_dir))

    # Set standard test credentials
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234")
    if "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" not in os.environ:
        monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false")

    # Explicitly disable file logging for tests
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    # Change to the project directory
    os.chdir(project_dir)

    # Patch logging to use in-memory handlers or temp paths
    with patch("devsynth.logging_setup.configure_logging") as mock_configure_logging:
        # Also patch ensure_path_exists to prevent directory creation
        with patch("devsynth.config.settings.ensure_path_exists") as mock_ensure_path:
            # Make ensure_path_exists return the path without creating it
            mock_ensure_path.side_effect = lambda path, create=True: path

            # Store test environment for tests that need it
            test_env = {
                "project_dir": project_dir,
                "logs_dir": logs_dir,
                "memory_dir": memory_dir,
                "devsynth_dir": devsynth_dir,
                "config_dir": config_dir,
                "checkpoints_dir": checkpoints_dir,
                "workflows_dir": workflows_dir,
            }

            # Run the test
            yield test_env

    # Restore original working directory
    os.chdir(original_cwd)

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

    # Clean up any stray files in real directories
    # Instead of relying on file modification times, we'll use a more reliable approach
    # by checking for specific directories that should never be created during tests
    real_paths_to_check = [
        Path(original_cwd) / "logs",
        Path(original_cwd) / ".devsynth",
        Path.home() / ".devsynth",
    ]

    for path in real_paths_to_check:
        if path.exists() and path.is_dir() and tmp_path not in path.parents:
            try:
                print(f"Cleaning up test artifact: {path}")
                shutil.rmtree(path)
            except (PermissionError, OSError) as e:
                # Log the error but don't fail the test
                print(f"Warning: Failed to clean up {path}: {str(e)}")


@pytest.fixture(autouse=True)
def disable_network(monkeypatch):
    """Disable network access during tests."""

    def guard_connect(*args, **kwargs):
        raise RuntimeError("Network access disabled during tests")

    monkeypatch.setattr(socket.socket, "connect", guard_connect)


@pytest.fixture
def mock_openai_provider():
    """
    Mock the OpenAI provider to prevent real API calls in tests.
    """
    with patch("devsynth.adapters.provider_system.OpenAIProvider") as mock_provider:
        # Configure the mock to return sensible test responses
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "Test completion response"
        mock_instance.embed.return_value = [0.1, 0.2, 0.3, 0.4]
        mock_provider.return_value = mock_instance
        yield mock_provider


@pytest.fixture
def mock_lm_studio_provider():
    """
    Mock the LM Studio provider to prevent real API calls in tests.
    """
    with patch("devsynth.adapters.provider_system.LMStudioProvider") as mock_provider:
        # Configure the mock to return sensible test responses
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "Test completion response"
        mock_instance.embed.return_value = [0.1, 0.2, 0.3, 0.4]
        mock_provider.return_value = mock_instance
        yield mock_provider


@pytest.fixture
def reset_global_state():
    """
    Reset any module-level global state between tests.

    This fixture helps ensure that tests don't affect each other through shared global variables.
    Add imports and resets for any modules with global state.
    """
    # Implementation will reset specific global variables in the codebase
    # Store original state
    from devsynth.logging_setup import (
        _logging_configured,
        _configured_log_dir,
        _configured_log_file,
    )

    orig_logging_configured = _logging_configured
    orig_log_dir = _configured_log_dir
    orig_log_file = _configured_log_file

    yield

    # Reset to original state
    import devsynth.logging_setup

    devsynth.logging_setup._logging_configured = orig_logging_configured
    devsynth.logging_setup._configured_log_dir = orig_log_dir
    devsynth.logging_setup._configured_log_file = orig_log_file

    # Reset any other global state across modules
    # Example: devsynth.some_module.global_variable = original_value


def is_lmstudio_available() -> bool:
    """Check if LM Studio is available."""
    # By default assume LM Studio is unavailable to avoid network calls
    if os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false").lower() not in (
        "1",
        "true",
        "yes",
    ):
        return False

    endpoint = os.environ.get("LM_STUDIO_ENDPOINT", "http://localhost:1234")

    try:
        import requests

        response = requests.get(f"{endpoint.rstrip('/')}/v1/models", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def is_codebase_available() -> bool:
    """Check if the DevSynth codebase is available for analysis."""
    # Check environment variable override
    if (
        os.environ.get("DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE", "true").lower()
        == "false"
    ):
        return False

    # Actual availability check
    try:
        # Check if the src directory exists
        return Path("src/devsynth").exists()
    except Exception:
        return False


def is_cli_available() -> bool:
    """Check if the DevSynth CLI is available for testing."""
    # Check environment variable override
    if os.environ.get("DEVSYNTH_RESOURCE_CLI_AVAILABLE", "true").lower() == "false":
        return False


def is_chromadb_available() -> bool:
    """Check if the chromadb package is installed."""
    if os.environ.get("DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE", "true").lower() == "false":
        return False
    try:  # pragma: no cover - simple import check
        import chromadb  # noqa: F401
        return True
    except Exception:
        return False


def is_faiss_available() -> bool:
    """Check if the faiss package is installed."""
    if os.environ.get("DEVSYNTH_RESOURCE_FAISS_AVAILABLE", "true").lower() == "false":
        return False
    try:  # pragma: no cover - simple import check
        import faiss  # noqa: F401
        return True
    except Exception:
        return False


def is_kuzu_available() -> bool:
    """Check if the kuzu package is installed."""
    if os.environ.get("DEVSYNTH_RESOURCE_KUZU_AVAILABLE", "true").lower() == "false":
        return False
    try:  # pragma: no cover - simple import check
        import kuzu  # noqa: F401
        return True
    except Exception:
        return False


def is_lmdb_available() -> bool:
    """Check if the lmdb package is installed."""
    if os.environ.get("DEVSYNTH_RESOURCE_LMDB_AVAILABLE", "true").lower() == "false":
        return False
    try:  # pragma: no cover - simple import check
        import lmdb  # noqa: F401
        return True
    except Exception:
        return False

    # Actual availability check
    try:
        import subprocess

        result = subprocess.run(["devsynth", "--help"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def is_resource_available(resource: str) -> bool:
    """
    Check if a resource is available.

    Parameters
    ----------
    resource : str
        The name of the resource to check

    Returns
    -------
    bool
        True if the resource is available, False otherwise
    """
    # Map resource names to checker functions
    checker_map = {
        "lmstudio": is_lmstudio_available,
        "codebase": is_codebase_available,
        "cli": is_cli_available,
        "chromadb": is_chromadb_available,
        "faiss": is_faiss_available,
        "kuzu": is_kuzu_available,
        "lmdb": is_lmdb_available,
    }

    # Get the checker function for the resource
    checker = checker_map.get(resource)
    if checker is None:
        # If no checker is defined, assume the resource is available
        return True

    # Call the checker function
    return checker()


def pytest_collection_modifyitems(config, items):
    """
    Skip tests that depend on external resources unless explicitly marked.
    Mark expected failures based on known issues.
    """
    for item in items:
        # Check for resource markers
        for marker in item.iter_markers(name="requires_resource"):
            resource = marker.args[0]
            if not is_resource_available(resource):
                # Skip the test if the resource is not available
                item.add_marker(
                    pytest.mark.skip(reason=f"Resource '{resource}' not available")
                )
