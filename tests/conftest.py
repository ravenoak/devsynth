"""
Configuration for pytest with comprehensive test isolation.

This module provides fixtures for ensuring all tests are hermetic (isolated from side effects)
and don't pollute the developer's environment, file system, or depend on external services.
"""

pytest_plugins = ["tests.conftest_extensions"]

import logging
import os
import random
import shutil
import socket
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Normalized subsystem stubs (GUI/providers)
try:
    from tests.fixtures.mock_subsystems import apply_normalized_stubs
except Exception:  # pragma: no cover - fallback if pathing changes
    apply_normalized_stubs = None  # type: ignore

try:
    import yaml
except ModuleNotFoundError:  # yaml is optional
    yaml = None

try:
    import coverage
except ModuleNotFoundError:  # coverage is optional
    coverage = None

try:
    from devsynth.config.settings import ensure_path_exists
except ModuleNotFoundError:

    def ensure_path_exists(path: str) -> str:
        Path(path).mkdir(parents=True, exist_ok=True)
        return path


# Add a marker for tests requiring external resources
requires_resource = pytest.mark.requires_resource


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_resource(name): mark test as requiring an external resource",
    )
    config.addinivalue_line(
        "markers",
        "property: mark test as a Hypothesis property-based test",
    )

    # Limit worker restarts to avoid xdist hangs when collecting coverage
    if (
        hasattr(config.option, "maxworkerrestart")
        and config.option.maxworkerrestart is None
    ):
        config.option.maxworkerrestart = 2


@pytest.fixture(scope="session", autouse=True)
def deterministic_seed() -> int:
    """Ensure deterministic behavior across tests by setting global RNG seeds.

    This fixture sets deterministic seeds for Python's random module and, when available,
    NumPy and PyTorch. It also ensures DEVSYNTH_TEST_SEED is present in the environment and
    attempts to propagate PYTHONHASHSEED for child processes. While PYTHONHASHSEED must be
    set before process start to fully affect hash randomization in this process, exporting it
    still benefits any subprocesses spawned by tests.

    Environment variables:
    - DEVSYNTH_TEST_SEED: overrides the default seed (defaults to "1337").
    - PYTHONHASHSEED: exported for subprocess determinism when not already set.

    Returns:
    - The integer seed applied.

    Rationale: Supports docs/tasks.md item 14 "Test suite health" -> "Ensure deterministic behavior where
    randomness present (seed fixtures)" and aligns with .junie/guidelines.md on reproducibility.
    """
    logger = logging.getLogger("tests.deterministic_seed")

    seed_env = os.environ.get("DEVSYNTH_TEST_SEED", "1337")
    try:
        seed = int(seed_env)
    except ValueError:
        # Fallback to a stable default if provided value is not an int
        logger.warning("Invalid DEVSYNTH_TEST_SEED=%r; falling back to 1337", seed_env)
        seed = 1337
        os.environ["DEVSYNTH_TEST_SEED"] = str(seed)

    # Export PYTHONHASHSEED for any subprocesses; note: too late to affect current interpreter
    if "PYTHONHASHSEED" not in os.environ:
        os.environ["PYTHONHASHSEED"] = str(seed)
        logger.debug("Set PYTHONHASHSEED=%s for subprocess determinism", seed)

    # Seed standard library RNG
    random.seed(seed)

    # Seed NumPy if available
    try:
        import numpy as np  # type: ignore

        np.random.seed(seed)
    except Exception as e:  # noqa: BLE001 - broad to avoid optional dep issues
        logger.debug("NumPy not available or failed to seed: %s", e)

    # Seed PyTorch if available
    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if torch.cuda.is_available():  # type: ignore[attr-defined]
            try:
                torch.cuda.manual_seed_all(seed)  # type: ignore[attr-defined]
            except Exception as ce:  # noqa: BLE001
                logger.debug("Failed to seed CUDA RNGs: %s", ce)
        # Favor determinism over perf in CI
        try:
            import torch.backends.cudnn as cudnn  # type: ignore

            cudnn.deterministic = True  # type: ignore[attr-defined]
            cudnn.benchmark = False  # type: ignore[attr-defined]
        except Exception as be:  # noqa: BLE001
            logger.debug("Failed to set cuDNN deterministic flags: %s", be)
    except Exception as e:  # noqa: BLE001
        logger.debug("PyTorch not available or failed to seed: %s", e)

    # Always expose the seed for tests that may want to assert or log it
    os.environ["DEVSYNTH_TEST_SEED"] = str(seed)
    logger.info("Deterministic test seed set to %s", seed)
    return seed


@pytest.fixture
def test_environment(tmp_path, monkeypatch):
    """Create a completely isolated test environment with temporary directories and patched environment variables. ReqID: none
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
    # Create project.yaml for the config loader
    with open(devsynth_dir / "project.yaml", "w") as f:
        f.write("language: python\n")

    # Provide the environment information to tests
    env_info = {
        "project_dir": project_dir,
        "logs_dir": logs_dir,
        "memory_dir": memory_dir,
        "devsynth_dir": devsynth_dir,
    }
    yield env_info
    # Temporary directories created under tmp_path are cleaned up automatically


@pytest.fixture(autouse=True)
def reset_coverage() -> None:
    """Reset coverage data between tests to prevent cross-worker hangs."""
    if coverage and os.environ.get("PYTEST_XDIST_WORKER"):
        cov = coverage.Coverage.current()
        if cov:
            cov.erase()


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
    # Also write a project.yaml file for the unified loader
    with open(temp_dir / ".devsynth" / "project.yaml", "w") as f:
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
def global_test_isolation(monkeypatch, tmp_path, reset_global_state):
    """
    Global fixture to ensure all tests are properly isolated.

    This autoused fixture:
    1. Saves and restores all environment variables
    2. Saves and restores the working directory
    3. Creates a temporary test environment
    4. Patches paths to use temporary directories
    5. Disables file logging for tests
    6. Patches logging configuration
    7. Resets project-level globals
    8. Cleans up any artifacts after tests

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

    # Establish a temporary HOME for tests to enforce tmp-only writes
    home_dir = tmp_path / "home"
    home_dir.mkdir(exist_ok=True)
    # Common XDG locations under HOME
    (home_dir / ".cache").mkdir(exist_ok=True)
    (home_dir / ".config").mkdir(exist_ok=True)
    (home_dir / ".local" / "share").mkdir(parents=True, exist_ok=True)

    # Set up a basic project structure
    with open(devsynth_dir / "config.json", "w") as f:
        f.write('{"model": "test-model", "project_name": "test-project"}')

    # Set environment variables to use temporary directories
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    monkeypatch.setenv("DEVSYNTH_LOG_DIR", str(logs_dir))
    monkeypatch.setenv("DEVSYNTH_MEMORY_PATH", str(memory_dir))
    monkeypatch.setenv("DEVSYNTH_CHECKPOINTS_PATH", str(checkpoints_dir))
    monkeypatch.setenv("DEVSYNTH_WORKFLOWS_PATH", str(workflows_dir))

    # Redirect HOME (and Windows USERPROFILE) to temporary directory
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("USERPROFILE", str(home_dir))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home_dir / ".cache"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home_dir / ".config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home_dir / ".local" / "share"))

    # Patch Path.home() to return the temporary HOME
    monkeypatch.setattr(Path, "home", lambda: home_dir)

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

    # Undo any monkeypatches from the test before running cleanup logic
    monkeypatch.undo()

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
    """Disable network access during tests.

    In addition to patching raw sockets, defensively patch common HTTP clients
    (requests, httpx, urllib) when available to ensure no network egress can occur.
    This aligns with docs/plan.md's isolation goals and .junie/guidelines.md on
    hermetic tests.
    """

    def guard_connect(*args, **kwargs):
        raise RuntimeError("Network access disabled during tests")

    # Block low-level sockets
    monkeypatch.setattr(socket.socket, "connect", guard_connect)

    # Block urllib to catch stdlib network attempts
    try:  # pragma: no cover - depends on optional import path usage
        import urllib.request as _urllib_request  # type: ignore

        def _guard_urlopen(*args, **kwargs):  # type: ignore
            raise RuntimeError("Network access disabled during tests (urllib)")

        monkeypatch.setattr(_urllib_request, "urlopen", _guard_urlopen, raising=False)
    except Exception:
        pass

    # Block requests if installed
    try:  # pragma: no cover - depends on optional dependency
        import requests  # type: ignore

        def guard_request(*args, **kwargs):  # type: ignore
            raise RuntimeError("Network access disabled during tests (requests)")

        # Session.request is used by all verbs
        monkeypatch.setattr(requests.sessions.Session, "request", guard_request, raising=True)  # type: ignore
        # Also patch top-level helper in case a library calls requests.api.request
        monkeypatch.setattr(requests.api, "request", guard_request, raising=False)  # type: ignore
    except Exception:
        pass

    # Block httpx if installed
    try:  # pragma: no cover - depends on optional dependency
        import httpx  # type: ignore

        def guard_httpx_request(*args, **kwargs):  # type: ignore
            raise RuntimeError("Network access disabled during tests (httpx)")

        monkeypatch.setattr(httpx.Client, "request", guard_httpx_request, raising=False)  # type: ignore
        monkeypatch.setattr(httpx.AsyncClient, "request", guard_httpx_request, raising=False)  # type: ignore
    except Exception:
        pass


@pytest.fixture(autouse=True)
def normalize_subsystem_stubs():
    """Apply normalized stubs for GUI and provider subsystems by default.

    - Honors env vars:
      - DEVSYNTH_TEST_ALLOW_GUI
      - DEVSYNTH_TEST_ALLOW_PROVIDERS
    - No-ops if helper is unavailable.
    """
    if apply_normalized_stubs is not None:
        apply_normalized_stubs()


@pytest.fixture(autouse=True)
def enforce_test_timeout(monkeypatch):
    """Enforce a per-test timeout to fail fast during fast/smoke runs.

    Controlled by the environment variable ``DEVSYNTH_TEST_TIMEOUT_SECONDS``.
    If set to a positive integer and the platform supports ``signal.SIGALRM``,
    a timeout alarm will abort tests that exceed the configured seconds with a
    clear RuntimeError. On platforms without SIGALRM (e.g., Windows), this
    fixture is a no-op.

    Rationale:
    - Supports docs/tasks.md item 38: reduce test timeouts to fail fast.
    - Aligns with .junie/guidelines.md preference for deterministic, quick feedback.
    """
    import os
    import sys

    timeout_str = os.environ.get("DEVSYNTH_TEST_TIMEOUT_SECONDS")
    if not timeout_str:
        return

    try:
        timeout = int(timeout_str)
    except Exception:
        return

    if timeout <= 0:
        return

    # Only apply on POSIX platforms that support SIGALRM
    try:
        import signal
    except Exception:
        return

    if not hasattr(signal, "SIGALRM"):
        return

    def _handler(signum, frame):  # noqa: ARG001 - signature required by signal
        raise RuntimeError(
            f"Test timed out after {timeout} seconds (DEVSYNTH_TEST_TIMEOUT_SECONDS)"
        )

    # Save original handler and set the alarm for each test
    original = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(timeout)
    try:
        yield
    finally:
        try:
            signal.alarm(0)  # cancel
            signal.signal(signal.SIGALRM, original)
        except Exception:
            # Best-effort cleanup; do not fail tests on teardown
            pass


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
        _configured_log_dir,
        _configured_log_file,
        _logging_configured,
    )

    orig_logging_configured = _logging_configured
    orig_log_dir = _configured_log_dir
    orig_log_file = _configured_log_file

    yield

    # Reset to original state
    import devsynth.logging_setup

    # Terminate any LM Studio websocket threads started during the test
    try:  # pragma: no cover - only runs if lmstudio is installed
        import lmstudio.sync_api as _ls_sync

        _ls_sync._reset_default_client()
    except Exception:
        pass

    logging.shutdown()

    devsynth.logging_setup._logging_configured = orig_logging_configured
    devsynth.logging_setup._configured_log_dir = orig_log_dir
    devsynth.logging_setup._configured_log_file = orig_log_file

    # Ensure coverage collectors don't leak between tests
    try:  # pragma: no cover - cleanup best effort
        import coverage
        from coverage import collector

        cov = coverage.Coverage.current()
        if cov:
            cov.stop()
        collector._collectors.clear()
    except Exception:
        pass

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
    except Exception:
        return False

    try:
        response = requests.get(f"{endpoint.rstrip('/')}/v1/models", timeout=0.2)
        return response.status_code == 200
    except requests.Timeout:
        return False
    except Exception:
        return False


def is_codebase_available() -> bool:
    """Check if the DevSynth codebase is available for analysis.

    Default behavior: available (True) unless explicitly disabled via
    DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE=false. This aligns with docs/tasks.md
    expectation for CI/local defaults.
    """
    # Respect explicit opt-out
    if (
        os.environ.get("DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE", "true").lower()
        == "false"
    ):
        return False

    # Actual availability check (best effort)
    try:
        return Path("src/devsynth").exists()
    except Exception:
        # If in doubt, assume available to avoid over-skipping
        return True


def is_cli_available() -> bool:
    """Check if the DevSynth CLI is available for testing.

    Default behavior: available (True) unless explicitly disabled via
    DEVSYNTH_RESOURCE_CLI_AVAILABLE=false. When available, optionally sanity-check
    that invoking `devsynth --help` succeeds; failures fall back to True to avoid
    over-skipping in environments without the entry-point.
    """
    # Respect explicit opt-out
    if os.environ.get("DEVSYNTH_RESOURCE_CLI_AVAILABLE", "true").lower() == "false":
        return False
    # Best-effort health check
    try:
        import subprocess

        proc = subprocess.run(["devsynth", "--help"], capture_output=True, text=True)
        return proc.returncode == 0
    except Exception:
        # Assume available if the subprocess cannot be executed in this environment
        return True


def is_webui_available() -> bool:
    """Check if the WebUI is available."""
    return os.environ.get("DEVSYNTH_RESOURCE_WEBUI_AVAILABLE", "false").lower() in {
        "1",
        "true",
        "yes",
    }


def is_chromadb_available() -> bool:
    """Check if the chromadb package is installed."""
    # Check environment variable override first
    if os.environ.get("DEVSYNTH_FORCE_CHROMADB_AVAILABLE", "false").lower() == "true":
        return True

    # Check if chromadb is installed
    try:  # pragma: no cover - simple import check
        import chromadb  # noqa: F401

        return True
    except ImportError:
        # Print a clear error message
        print(
            "\n\033[91mWARNING: chromadb package is not installed but is required for memory integration tests.\033[0m"
        )
        print(
            "\033[93mTo install chromadb, run: poetry install --extras chromadb\033[0m"
        )
        print(
            "\033[93mOr to install all memory dependencies: poetry install --extras memory\033[0m"
        )
        print(
            "\033[93mTo skip these tests, set DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=false\033[0m\n"
        )

        # Check if we're running in CI environment
        if os.environ.get("CI", "false").lower() == "true":
            # In CI, we want to fail rather than skip
            return True

        # For local development, respect the resource availability flag
        if (
            os.environ.get("DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE", "true").lower()
            == "false"
        ):
            return False

        # Default behavior: return False to skip tests requiring chromadb
        return False


def is_tinydb_available() -> bool:
    """Check if the tinydb package is installed."""
    if os.environ.get("DEVSYNTH_RESOURCE_TINYDB_AVAILABLE", "true").lower() == "false":
        return False
    try:  # pragma: no cover - simple import check
        import tinydb  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def is_duckdb_available() -> bool:
    """Check if the duckdb package is installed."""
    if os.environ.get("DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE", "true").lower() == "false":
        return False
    try:  # pragma: no cover - simple import check
        import duckdb  # type: ignore  # noqa: F401

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


def is_rdflib_available() -> bool:
    """Check if the rdflib package is installed."""
    if os.environ.get("DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE", "true").lower() == "false":
        return False
    try:  # pragma: no cover - simple import check
        import rdflib  # noqa: F401

        return True
    except Exception:
        return False


def is_openai_available() -> bool:
    """Check if OpenAI is configured via API key."""
    if os.environ.get("DEVSYNTH_RESOURCE_OPENAI_AVAILABLE", "true").lower() == "false":
        return False
    return bool(os.environ.get("OPENAI_API_KEY"))


def is_memory_available() -> bool:
    """Generic 'memory' resource gate for memory-heavy tests (opt-out via env)."""
    return os.environ.get("DEVSYNTH_RESOURCE_MEMORY_AVAILABLE", "true").lower() != "false"


def is_test_resource_available() -> bool:
    """Test sentinel resource used by unit tests to validate resource gating."""
    return os.environ.get("DEVSYNTH_RESOURCE_TEST_RESOURCE_AVAILABLE", "false").lower() == "true"


def is_anthropic_available() -> bool:
    """Check if the anthropic package and API key are available."""
    if (
        os.environ.get("DEVSYNTH_RESOURCE_ANTHROPIC_AVAILABLE", "true").lower()
        == "false"
    ):
        return False
    try:  # pragma: no cover - simple import check
        import anthropic  # noqa: F401

    except Exception:
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def is_llm_provider_available() -> bool:
    """Check if a real LLM provider is configured."""
    if (
        os.environ.get("DEVSYNTH_RESOURCE_LLM_PROVIDER_AVAILABLE", "true").lower()
        == "false"
    ):
        return False
    return bool(
        os.environ.get("OPENAI_API_KEY") or os.environ.get("LM_STUDIO_ENDPOINT")
    )


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
        "anthropic": is_anthropic_available,
        "llm_provider": is_llm_provider_available,
        "lmstudio": is_lmstudio_available,
        "openai": is_openai_available,
        "codebase": is_codebase_available,
        "cli": is_cli_available,
        "chromadb": is_chromadb_available,
        "tinydb": is_tinydb_available,
        "duckdb": is_duckdb_available,
        "faiss": is_faiss_available,
        "kuzu": is_kuzu_available,
        "lmdb": is_lmdb_available,
        "rdflib": is_rdflib_available,
        "memory": is_memory_available,
        "test_resource": is_test_resource_available,
        "webui": is_webui_available,
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

    # Skip property-based tests unless enabled
    for item in items:
        if item.get_closest_marker("property") and not is_property_testing_enabled():
            item.add_marker(pytest.mark.skip(reason="Property testing disabled"))


def is_property_testing_enabled() -> bool:
    """Return True if property-based tests should run."""
    flag = os.environ.get("DEVSYNTH_PROPERTY_TESTING")
    if flag is not None:
        return flag.strip().lower() in {"1", "true", "yes"}
    cfg_path = Path(__file__).resolve().parents[1] / "config" / "default.yml"
    try:
        with open(cfg_path, "r") as f:
            data = yaml.safe_load(f) or {}
        return bool(data.get("formalVerification", {}).get("propertyTesting", False))
    except Exception:
        return False
