"""
Configuration for pytest with comprehensive test isolation.

This module provides fixtures for ensuring all tests are hermetic (isolated from side effects)
and don't pollute the developer's environment, file system, or depend on external services.
"""

import sys

# Load sitecustomize early for Python 3.12+ compatibility patches
import sitecustomize  # noqa: F401

pytest_plugins = [
    "tests.conftest_extensions",
    "tests.fixtures.backends",
    "tests.fixtures.ports",
    "tests.fixtures.kuzu",
    "tests.fixtures.state_access_fixture",
    "tests.fixtures.webui_wizard_state_fixture",
    "tests.fixtures.optional_deps",
    "tests.fixtures.lmstudio_mock",
    "tests.fixtures.lmstudio_service",
    "tests.fixtures.webui_bridge_stub",
    "tests.fixtures.webui_test_utils",
    "tests.unit.testing",
    "pytester",
]

import importlib.util
from importlib import import_module
from importlib.machinery import ModuleSpec

from tests import pytest_plugin_registry as _pytest_plugin_registry
from tests.fixtures.optional_deps import _apply_optional_stubs, stub_optional_deps

# Apply optional dependency stubs globally for resource availability checks
_apply_optional_stubs()


def _load_additional_pytest_plugins(module_name: str) -> None:
    """Extend ``pytest_plugins`` with entries exported from helper modules."""

    try:
        module = import_module(module_name)
    except Exception:
        return
    plugin_names = getattr(module, "PYTEST_PLUGINS", None)
    if not plugin_names:
        plugin_names = getattr(module, "pytest_plugins", None)
    if not plugin_names:
        return
    for plugin_name in plugin_names:
        target_name = _PLUGIN_REDIRECTS.get(plugin_name, plugin_name)
        if target_name not in pytest_plugins:
            pytest_plugins.append(target_name)


_ADDITIONAL_PYTEST_PLUGIN_PROVIDERS = [
    _pytest_plugin_registry.__name__,
]

# Plugin redirects are unnecessary now that optional plugins (for example,
# ``pytest_bdd.plugin``) are resolved through ``tests.pytest_plugin_registry``
# before being appended to ``pytest_plugins``.
_PLUGIN_REDIRECTS = {}

for _provider in _ADDITIONAL_PYTEST_PLUGIN_PROVIDERS:
    _load_additional_pytest_plugins(_provider)
del _provider
del _pytest_plugin_registry

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

# Configure Hypothesis defaults for property-based tests when available
try:  # pragma: no cover - only active when hypothesis is installed
    from hypothesis import HealthCheck, Phase, Verbosity, settings

    # Allow environment overrides for CI/local tuning
    _hyp_deadline = os.environ.get("DEVSYNTH_HYPOTHESIS_DEADLINE_MS", "500")
    _hyp_max_examples = os.environ.get("DEVSYNTH_HYPOTHESIS_MAX_EXAMPLES", "50")
    try:
        _deadline_ms = int(_hyp_deadline)
    except Exception:
        _deadline_ms = 500
    try:
        _max_examples = int(_hyp_max_examples)
    except Exception:
        _max_examples = 50

    settings.register_profile(
        "devsynth",
        settings(
            deadline=_deadline_ms,
            suppress_health_check=[HealthCheck.too_slow],
            phases=(Phase.explicit, Phase.generate, Phase.shrink),
            max_examples=_max_examples,
            verbosity=Verbosity.normal,
        ),
    )
    settings.load_profile(os.environ.get("DEVSYNTH_HYPOTHESIS_PROFILE", "devsynth"))
except Exception:
    # Hypothesis not installed or configuration failed; tests/property/ are skipped by gating anyway
    pass

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
    config.addinivalue_line(
        "markers",
        "performance: mark test as a performance/benchmark test (opt-in)",
    )
    # Register derived static markers for known resources to allow '-m resource_<name>' selection
    for _res in [
        "anthropic",
        "llm_provider",
        "lmstudio",
        "openai",
        "codebase",
        "cli",
        "chromadb",
        "tinydb",
        "duckdb",
        "faiss",
        "kuzu",
        "lmdb",
        "rdflib",
        "memory",
        "test_resource",
        "webui",
    ]:
        config.addinivalue_line(
            "markers",
            f"resource_{_res}: derived marker for requires_resource('{_res}')",
        )

    # Limit worker restarts to avoid xdist hangs when collecting coverage
    if (
        hasattr(config.option, "maxworkerrestart")
        and config.option.maxworkerrestart is None
    ):
        config.option.maxworkerrestart = 2


# Extracted to tests/fixtures/determinism.py
from tests.fixtures.determinism import deterministic_seed


@pytest.fixture(name="test_environment")
def _test_environment(tmp_path, monkeypatch):
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
    (temp_dir / ".devsynth").mkdir(parents=True, exist_ok=True)

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
def mock_datetime(monkeypatch):
    """
    Patch datetime.datetime.now/utcnow and time.time to return a fixed, timezone-stable value.

    Notes:
    - Uses a fixed naive datetime (interpreted consistently) and a fixed epoch timestamp for time.time.
    - Helps avoid wall-clock drift and timezone-related flakiness across platforms.
    """
    fixed_dt = datetime(2025, 1, 1, 12, 0, 0)
    # Patch datetime.datetime methods used by code under test
    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_dt
        mock_dt.utcnow.return_value = fixed_dt
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        # Patch time.time to a fixed timestamp derived from fixed_dt
        import time as _time  # local import to avoid global side effects

        fixed_ts = int(fixed_dt.timestamp())
        with patch.object(_time, "time", return_value=fixed_ts):
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

    # Enforce hermetic provider defaults unless explicitly overridden (docs/plan.md §8; project guidelines)
    if "DEVSYNTH_PROVIDER" not in os.environ:
        monkeypatch.setenv("DEVSYNTH_PROVIDER", "stub")
    if "DEVSYNTH_OFFLINE" not in os.environ:
        monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")

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


# Extracted to tests/fixtures/networking.py
from tests.fixtures.networking import disable_network


@pytest.fixture(autouse=True)
def stub_optional_dependencies(monkeypatch):
    """Apply stubs for optional dependencies to enable comprehensive testing.

    This fixture provides lightweight stubs for heavy optional dependencies,
    allowing tests to run even when optional packages are not installed.
    """
    stub_optional_deps(monkeypatch)


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


# Extracted to tests/fixtures/determinism.py
from tests.fixtures.determinism import enforce_test_timeout


@pytest.fixture(autouse=True)
def _default_timeout_by_speed(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Set a default per-test timeout based on speed markers when not explicitly set.

    Non-smoke defaults (local/dev):
    - fast: 3s (quick signal)
    - medium: 10s (integration guidance)
    - slow: 30s (generous cap; keep tests bounded)

    Smoke mode (plugins disabled via PYTEST_DISABLE_PLUGIN_AUTOLOAD=1):
    - fast: 2s
    - medium: 5s
    - slow: 15s

    This only applies when DEVSYNTH_TEST_TIMEOUT_SECONDS is not already set, so
    explicit CLI/env control remains authoritative. The actual enforcement is
    performed by tests.fixtures.determinism.enforce_test_timeout.
    """
    # Respect explicit configuration
    if os.environ.get("DEVSYNTH_TEST_TIMEOUT_SECONDS"):
        return

    # Determine if we're in smoke mode (plugins disabled)
    smoke = os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "0").lower() in {
        "1",
        "true",
        "yes",
    }

    # Determine closest speed marker and set default timeout accordingly
    if request.node.get_closest_marker("fast") is not None:
        monkeypatch.setenv("DEVSYNTH_TEST_TIMEOUT_SECONDS", "2" if smoke else "3")
    elif request.node.get_closest_marker("medium") is not None:
        monkeypatch.setenv("DEVSYNTH_TEST_TIMEOUT_SECONDS", "5" if smoke else "10")
    elif request.node.get_closest_marker("slow") is not None:
        # Provide an upper bound while allowing intentionally longer tests
        monkeypatch.setenv("DEVSYNTH_TEST_TIMEOUT_SECONDS", "15" if smoke else "30")


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


def _safe_find_spec(name: str) -> ModuleSpec | None:
    """Return the module spec for ``name`` when available."""

    try:  # pragma: no cover - importlib behaviours differ across environments
        spec = importlib.util.find_spec(name)
    except (ImportError, AttributeError, ValueError):
        return None
    return spec


def _spec_is_importable(spec: ModuleSpec | None) -> bool:
    """Return ``True`` when ``spec`` represents an importable module."""

    if spec is None:
        return False
    loader = getattr(spec, "loader", None)
    submodule_locations = getattr(spec, "submodule_search_locations", ()) or ()
    if loader is None and not submodule_locations:
        return False
    if getattr(spec, "has_location", True) is False and not submodule_locations:
        return False
    origin = getattr(spec, "origin", None)
    if origin in {None, "namespace"} and not submodule_locations:
        return False
    return True


def is_chromadb_available() -> bool:
    """Check if the chromadb package is available (real or stubbed)."""
    if os.environ.get("DEVSYNTH_FORCE_CHROMADB_AVAILABLE", "false").lower() == "true":
        return True

    # Check if real package is available
    spec = _safe_find_spec("chromadb")
    if _spec_is_importable(spec):
        return True

    # Check if stub is available
    if "chromadb" in sys.modules and hasattr(sys.modules["chromadb"], "Client"):
        return True

    print(
        "\n\033[91mWARNING: chromadb package is not installed but is required for memory integration tests.\033[0m"
    )
    print("\033[93mTo install chromadb, run: poetry install --extras chromadb\033[0m")
    print(
        "\033[93mOr to install all memory dependencies: poetry install --extras memory\033[0m"
    )
    print(
        "\033[93mTo skip these tests, set DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=false\033[0m\n"
    )

    if os.environ.get("CI", "false").lower() == "true":
        return True

    if (
        os.environ.get("DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE", "true").lower()
        == "false"
    ):
        return False

    return False


def is_tinydb_available() -> bool:
    """Check if the tinydb package is available (real or stubbed)."""
    if os.environ.get("DEVSYNTH_RESOURCE_TINYDB_AVAILABLE", "true").lower() == "false":
        return False

    # Check if real package is available
    if _spec_is_importable(_safe_find_spec("tinydb")):
        return True

    # Check if stub is available
    if "tinydb" in sys.modules and hasattr(sys.modules["tinydb"], "TinyDB"):
        return True

    return False


def is_duckdb_available() -> bool:
    """Check if the duckdb package is available (real or stubbed)."""
    if os.environ.get("DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE", "true").lower() == "false":
        return False

    # Check if real package is available
    if _spec_is_importable(_safe_find_spec("duckdb")):
        return True

    # Check if stub is available
    if "duckdb" in sys.modules and hasattr(sys.modules["duckdb"], "connect"):
        return True

    return False


def is_faiss_available() -> bool:
    """Check if the faiss package is available (real or stubbed)."""
    if os.environ.get("DEVSYNTH_RESOURCE_FAISS_AVAILABLE", "true").lower() == "false":
        return False

    # Check if real package is available
    if _spec_is_importable(_safe_find_spec("faiss")):
        return True

    # Check if stub is available
    if "faiss" in sys.modules and hasattr(sys.modules["faiss"], "IndexFlatIP"):
        return True

    return False


def is_kuzu_available() -> bool:
    """Check if the kuzu package is available (real or stubbed)."""
    if os.environ.get("DEVSYNTH_RESOURCE_KUZU_AVAILABLE", "true").lower() == "false":
        return False

    # Check if real package is available
    if _spec_is_importable(_safe_find_spec("kuzu")):
        return True

    # Check if stub is available
    if "kuzu" in sys.modules and hasattr(sys.modules["kuzu"], "Database"):
        return True

    return False


def is_lmdb_available() -> bool:
    """Check if the lmdb package is available (real or stubbed)."""
    if os.environ.get("DEVSYNTH_RESOURCE_LMDB_AVAILABLE", "true").lower() == "false":
        return False

    # Check if real package is available
    if _spec_is_importable(_safe_find_spec("lmdb")):
        return True

    # Check if stub is available
    if "lmdb" in sys.modules and hasattr(sys.modules["lmdb"], "open"):
        return True

    return False


def is_vector_available() -> bool:
    """Check if numpy is available for vector-backed tests (real or stubbed)."""

    if os.environ.get("DEVSYNTH_RESOURCE_VECTOR_AVAILABLE", "true").lower() == "false":
        return False

    # Check if real package is available
    if _spec_is_importable(_safe_find_spec("numpy")):
        return True

    # Check if stub is available
    if "numpy" in sys.modules and hasattr(sys.modules["numpy"], "array"):
        return True

    return False


def is_rdflib_available() -> bool:
    """Check if the rdflib package is available (real or stubbed)."""
    if os.environ.get("DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE", "true").lower() == "false":
        return False

    # Check if real package is available
    if _spec_is_importable(_safe_find_spec("rdflib")):
        return True

    # Check if stub is available
    if "rdflib" in sys.modules and hasattr(sys.modules["rdflib"], "Graph"):
        return True

    return False


def is_openai_available() -> bool:
    """Check if OpenAI is configured via API key."""
    if os.environ.get("DEVSYNTH_RESOURCE_OPENAI_AVAILABLE", "true").lower() == "false":
        return False
    return bool(os.environ.get("OPENAI_API_KEY"))


def is_memory_available() -> bool:
    """Generic 'memory' resource gate for memory-heavy tests (opt-out via env)."""
    return (
        os.environ.get("DEVSYNTH_RESOURCE_MEMORY_AVAILABLE", "true").lower() != "false"
    )


def is_test_resource_available() -> bool:
    """Test sentinel resource used by unit tests to validate resource gating."""
    return (
        os.environ.get("DEVSYNTH_RESOURCE_TEST_RESOURCE_AVAILABLE", "false").lower()
        == "true"
    )


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
        "vector": is_vector_available,
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
    Normalize and enforce resource gating, smoke-mode behavior, property-based testing collection,
    and conservative xdist-parallel safety.

    - Resource gating: validate @pytest.mark.requires_resource("<name>") and skip when unavailable or malformed/unknown.
    - Smoke mode: when PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, skip tests under tests/behavior/ that rely on third-party plugins.
    - Property-based tests: skip unless DEVSYNTH_PROPERTY_TESTING is enabled.
    - Xdist safety: conservatively mark integration and performance tests as @pytest.mark.isolation to avoid parallelization issues.
    """
    # Validate and apply resource gating
    for item in items:
        for marker in item.iter_markers(name="requires_resource"):
            # Validate marker arguments
            if (
                not marker.args
                or not isinstance(marker.args[0], str)
                or not marker.args[0].strip()
            ):
                item.add_marker(
                    pytest.mark.skip(
                        reason="Malformed requires_resource marker: expected a non-empty resource name"
                    )
                )
                continue
            resource = marker.args[0].strip()

            # Validate known resource
            known_resources = {
                "anthropic",
                "llm_provider",
                "lmstudio",
                "openai",
                "codebase",
                "cli",
                "chromadb",
                "tinydb",
                "duckdb",
                "faiss",
                "kuzu",
                "lmdb",
                "rdflib",
                "memory",
                "test_resource",
                "webui",
            }
            if resource not in known_resources:
                item.add_marker(
                    pytest.mark.skip(
                        reason=f"Unknown resource '{resource}' not recognized by test harness"
                    )
                )
                continue

            # Add a derived static marker to enable '-m resource_<name>' selection
            try:
                item.add_marker(getattr(pytest.mark, f"resource_{resource}"))
            except Exception:
                # Defensive: do not fail collection if dynamic marker attachment has issues
                pass

            # Skip if resource is not available
            if not is_resource_available(resource):
                item.add_marker(
                    pytest.mark.skip(reason=f"Resource '{resource}' not available")
                )

    # Smoke-mode behavior: skip behavior tests when plugins are disabled
    smoke = os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "0").lower() in {
        "1",
        "true",
        "yes",
    }
    if smoke:
        skip_behavior = pytest.mark.skip(
            reason=(
                "Smoke mode (plugins disabled): skipping behavior tests that require third-party plugins"
            )
        )
        for item in items:
            try:
                fspath = getattr(item, "fspath", None)
                path_str = str(fspath) if fspath is not None else ""
            except Exception:
                path_str = ""
            norm = path_str.replace("\\", "/")
            if "/tests/behavior/" in norm or norm.endswith("/tests/behavior"):
                item.add_marker(skip_behavior)

    # Conservatively mark integration and performance tests as isolation for xdist safety
    for item in items:
        try:
            fspath = getattr(item, "fspath", None)
            path_str = str(fspath) if fspath is not None else ""
        except Exception:
            path_str = ""
        norm = path_str.replace("\\", "/")
        if "/tests/integration/" in norm or "/tests/performance/" in norm:
            if not item.get_closest_marker("isolation"):
                item.add_marker(pytest.mark.isolation)

    # Broaden isolation auto-marking heuristics for fragile tests that touch filesystem/network
    # Apply only when a test lacks an explicit @pytest.mark.isolation
    network_keywords = ("network", "http", "https", "socket", "requests", "ftp")
    fs_fixtures = {
        "tmp_path",
        "tmpdir",
        "tmpdir_factory",
        "temp_log_dir",
        "tmp_project_dir",
    }
    for item in items:
        try:
            name = getattr(item, "name", "") or ""
            nodeid = getattr(item, "nodeid", "") or ""
            fixturenames = set(getattr(item, "fixturenames", []) or [])
        except Exception:
            name, nodeid, fixturenames = "", "", set()
        if item.get_closest_marker("isolation"):
            continue
        name_l = name.lower()
        nodeid_l = nodeid.lower()
        touches_network = any(kw in name_l or kw in nodeid_l for kw in network_keywords)
        touches_fs = bool(fs_fixtures.intersection(fixturenames))
        if touches_network or touches_fs:
            try:
                item.add_marker(pytest.mark.isolation)
            except Exception:
                pass

    # Auto-inject a default speed marker for behavior (pytest-bdd) scenario wrappers that
    # lack an explicit function-level speed marker. This eliminates runtime warnings while
    # preserving the repository rule of exactly one speed marker per test function.
    # We only apply to tests under tests/behavior/ to avoid interfering with unit/integration
    # tests where speed markers must be explicitly present in source.
    for item in items:
        try:
            fspath = getattr(item, "fspath", None)
            path_str = str(fspath) if fspath is not None else ""
        except Exception:
            path_str = ""
        norm = path_str.replace("\\", "/")
        if "/tests/behavior/" in norm or norm.endswith("/tests/behavior"):
            # Check only own (function-level) markers to avoid counting module-level markers,
            # which are not recognized for speed categories per repository guidelines.
            own_marks = {m.name for m in getattr(item, "own_markers", [])}
            has_speed = any(m in {"fast", "medium", "slow"} for m in own_marks)
            if not has_speed:
                item.add_marker(pytest.mark.fast)

    # Skip property-based tests unless enabled
    for item in items:
        if item.get_closest_marker("property") and not is_property_testing_enabled():
            item.add_marker(pytest.mark.skip(reason="Property testing disabled"))


# Moved from tests/fixtures/resources.py to avoid circular import
def is_property_testing_enabled() -> bool:
    """Return True if property-based tests should run."""

    flag = os.environ.get("DEVSYNTH_PROPERTY_TESTING")
    if flag is not None:
        return flag.strip().lower() in {"1", "true", "yes"}

    cfg_path = Path(__file__).resolve().parent / "config" / "default.yml"
    try:
        import yaml

        with open(cfg_path) as f:  # type: ignore[call-arg]
            data: dict[str, Any] = yaml.safe_load(f) or {}
        return bool(data.get("formalVerification", {}).get("propertyTesting", False))
    except Exception:
        return False


def pytest_runtest_setup(item: pytest.Item) -> None:
    """
    When running under xdist workers, skip tests marked with @pytest.mark.isolation unless
    explicitly allowed via DEVSYNTH_ALLOW_ISOLATION_IN_XDIST=true. This prevents known
    shared-state or resource-contention issues from causing flakes under parallel execution.
    """
    allow_isolation = os.environ.get(
        "DEVSYNTH_ALLOW_ISOLATION_IN_XDIST", ""
    ).lower() in {"1", "true", "yes"}
    running_in_xdist = os.environ.get("PYTEST_XDIST_WORKER") is not None
    if (
        running_in_xdist
        and item.get_closest_marker("isolation")
        and not allow_isolation
    ):
        pytest.skip(
            "Isolation test skipped under xdist (parallel). Rerun with -n0/--no-parallel or set "
            "DEVSYNTH_ALLOW_ISOLATION_IN_XDIST=true to force-run in parallel."
        )


# NOTE: Merged into the unified pytest_collection_modifyitems above to avoid duplicate hook definitions.


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line option to enable limited retries for resource-marked tests.

    Controlled by either:
    - CLI: --devsynth-resource-retries N
    - Env: DEVSYNTH_RESOURCE_RETRIES=N (used if CLI not supplied)

    Default is 0 (disabled). This is intentionally scoped to resource-marked tests
    to keep unit tests deterministic and fast, per docs/plan.md Section "Key risks
    and mitigations" (retries=2 for online subsets).
    """
    parser.addoption(
        "--devsynth-resource-retries",
        action="store",
        dest="devsynth_resource_retries",
        default=None,
        help="Enable reruns for tests marked requires_resource; value is integer N (default 0).",
    )


def pytest_configure(config: pytest.Config):  # type: ignore[override]
    """Inject rerun configuration only for resource-marked tests.

    We leverage pytest-rerunfailures if installed. If the plugin is not available,
    we simply no-op. The rerun count is pulled from the CLI option above or from
    DEVSYNTH_RESOURCE_RETRIES env var. Scope is limited using the plugin's
    --reruns and --only-rerun marked expression support when available; otherwise
    we set a custom hook to re-schedule failures selectively.
    """
    try:
        import pytest_rerunfailures  # type: ignore  # noqa: F401
    except Exception:
        return  # plugin not installed, do nothing

    # Determine retries
    cli_val = config.getoption("devsynth_resource_retries", default=None)
    env_val = os.environ.get("DEVSYNTH_RESOURCE_RETRIES")
    retries = None
    if cli_val is not None:
        try:
            retries = int(cli_val)
        except Exception:
            retries = 0
    elif env_val is not None:
        try:
            retries = int(env_val)
        except Exception:
            retries = 0
    else:
        retries = 0

    if retries and retries > 0:
        # Configure plugin options programmatically. Prefer selective reruns via marker expression.
        # Newer pytest-rerunfailures supports --only-rerun <expr>.
        try:
            # Equivalent of: --reruns <retries> --only-rerun "requires_resource"
            setattr(config.option, "reruns", retries)
            setattr(config.option, "only_rerun", "requires_resource")
        except Exception:
            # Fallback: set global reruns (less ideal). We further reduce impact by
            # lowering retries for non-resource tests to 0 via a custom hook below.
            setattr(config.option, "reruns", retries)

            @pytest.hookimpl(hookwrapper=True, tryfirst=True)
            def pytest_runtest_makereport(item, call):  # type: ignore
                outcome = yield
                rep = outcome.get_result()
                # If the test is not resource-marked, clear reruns to avoid retrying it
                if not item.get_closest_marker("requires_resource"):
                    setattr(config.option, "reruns", 0)
                else:
                    setattr(config.option, "reruns", retries)
                return rep
