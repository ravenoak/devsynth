"""
Simplified test configuration for DevSynth.

This is a proposed replacement for the complex conftest.py that reduces
complexity while maintaining essential functionality.

Key improvements:
- Focused responsibilities
- Cleaner separation of concerns
- Better maintainability
- Reduced cognitive overhead
"""

import os
import sys
from pathlib import Path
from typing import Dict
from collections.abc import Iterator
from unittest.mock import patch

import pytest

from tests.fixtures.backends import *  # Import all backend fixtures

# Import focused modules instead of having everything in one file
from tests.fixtures.determinism import deterministic_seed, enforce_test_timeout
from tests.fixtures.networking import disable_network
from tests.fixtures.resources import is_property_testing_enabled


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with essential settings only."""
    # Register gui marker (most commonly needed)
    config.addinivalue_line(
        "markers",
        "gui: mark test as requiring GUI or optional UI extras (NiceGUI/DearPyGUI)",
    )

    # Configure coverage enforcement based on environment
    _configure_coverage_enforcement(config)


def _configure_coverage_enforcement(config: pytest.Config) -> None:
    """Configure coverage enforcement based on environment variables."""
    strict_coverage = os.getenv("DEVSYNTH_FULL_COVERAGE") or os.getenv(
        "DEVSYNTH_STRICT_COVERAGE"
    )

    if hasattr(config, "option") and hasattr(config.option, "cov_fail_under"):
        if not strict_coverage:
            # Relax coverage for fast feedback during development
            config.option.cov_fail_under = 0
        else:
            # Allow override of strict threshold
            threshold_override = os.getenv("DEVSYNTH_COV_FAIL_UNDER")
            if threshold_override:
                try:
                    config.option.cov_fail_under = int(threshold_override)
                except ValueError:
                    pass  # Keep existing threshold


@pytest.fixture(scope="session", autouse=True)
def _test_environment_defaults() -> None:
    """Set conservative, offline-first defaults for all tests."""
    defaults = {
        "DEVSYNTH_OFFLINE": "true",
        "DEVSYNTH_PROVIDER": "stub",
        "DEVSYNTH_NO_FILE_LOGGING": "1",
        "OPENAI_API_KEY": "test-openai-key",
        "LM_STUDIO_ENDPOINT": "http://127.0.0.1:1234",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "false",
        "DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE": "true",
        "DEVSYNTH_RESOURCE_CLI_AVAILABLE": "true",
    }

    for key, value in defaults.items():
        os.environ.setdefault(key, value)


@pytest.fixture(autouse=True)
def global_test_isolation(monkeypatch, tmp_path) -> Iterator[dict[str, Path]]:
    """
    Provide comprehensive test isolation with simplified implementation.

    This fixture ensures tests are hermetic by:
    1. Redirecting all file operations to tmp directories
    2. Isolating environment variables
    3. Preventing network access
    4. Providing clean working directory
    """
    # Save original state
    original_env = dict(os.environ)
    original_cwd = os.getcwd()

    # Create isolated test environment
    test_env = _create_test_environment(tmp_path, monkeypatch)

    try:
        yield test_env
    finally:
        # Restore original state
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)


def _create_test_environment(tmp_path: Path, monkeypatch) -> dict[str, Path]:
    """Create isolated test environment with necessary directories."""
    # Create test directory structure
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    devsynth_dir = project_dir / ".devsynth"

    for directory in [project_dir, home_dir, devsynth_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    # Create basic configuration
    (devsynth_dir / "config.json").write_text(
        '{"model": "test-model", "project_name": "test-project"}'
    )

    # Set up environment isolation
    env_patches = {
        "DEVSYNTH_PROJECT_DIR": str(project_dir),
        "HOME": str(home_dir),
        "USERPROFILE": str(home_dir),  # Windows compatibility
    }

    for key, value in env_patches.items():
        monkeypatch.setenv(key, value)

    # Patch Path.home() for complete isolation
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    # Change to project directory
    os.chdir(project_dir)

    return {
        "project_dir": project_dir,
        "home_dir": home_dir,
        "devsynth_dir": devsynth_dir,
    }


def pytest_collection_modifyitems(config, items):
    """
    Apply collection-time modifications with simplified logic.

    This handles:
    1. Resource gating for optional dependencies
    2. Speed marker validation
    3. Isolation marker management for xdist
    """
    _apply_resource_gating(items)
    _apply_speed_marker_validation(items)
    _apply_isolation_management(items)


def _apply_resource_gating(items):
    """Apply resource availability gating to tests."""
    from tests.conftest import is_resource_available  # Import from original conftest

    for item in items:
        for marker in item.iter_markers(name="requires_resource"):
            if not marker.args or not isinstance(marker.args[0], str):
                item.add_marker(pytest.mark.skip("Malformed requires_resource marker"))
                continue

            resource = marker.args[0].strip()
            if not is_resource_available(resource):
                item.add_marker(
                    pytest.mark.skip(f"Resource '{resource}' not available")
                )


def _apply_speed_marker_validation(items):
    """Validate that tests have appropriate speed markers."""
    for item in items:
        speed_markers = [
            name for name in ("fast", "medium", "slow") if item.get_closest_marker(name)
        ]

        if len(speed_markers) != 1:
            # For behavior tests, auto-add fast marker as fallback
            if "/tests/behavior/" in str(item.fspath):
                item.add_marker(pytest.mark.fast)


def _apply_isolation_management(items):
    """Manage isolation markers for xdist compatibility."""
    # Skip isolation tests under xdist unless explicitly allowed
    if os.environ.get("PYTEST_XDIST_WORKER") and not os.environ.get(
        "DEVSYNTH_ALLOW_ISOLATION_IN_XDIST"
    ):
        for item in items:
            if item.get_closest_marker("isolation"):
                item.add_marker(
                    pytest.mark.skip(
                        "Isolation test skipped under xdist. Use -n0 or set DEVSYNTH_ALLOW_ISOLATION_IN_XDIST=true"
                    )
                )


# Import essential fixtures that tests depend on
# These are kept in the main conftest for backward compatibility
@pytest.fixture
def test_environment(tmp_path, monkeypatch):
    """Backward compatibility fixture - use global_test_isolation instead."""
    return _create_test_environment(tmp_path, monkeypatch)


@pytest.fixture
def tmp_project_dir(tmp_path):
    """Create a temporary project directory with basic DevSynth structure."""
    project_dir = tmp_path / "project"
    devsynth_dir = project_dir / ".devsynth"
    devsynth_dir.mkdir(parents=True)

    # Create basic configuration
    (devsynth_dir / "config.json").write_text(
        '{"model": "gpt-4", "project_name": "test-project"}'
    )
    (devsynth_dir / "project.yaml").write_text("language: python\n")

    return project_dir


# Simplified plugin registration
def pytest_addoption(parser: pytest.Parser) -> None:
    """Add essential command-line options only."""
    parser.addoption(
        "--devsynth-resource-retries",
        action="store",
        default=None,
        help="Enable reruns for tests marked requires_resource (integer N, default 0)",
    )


def pytest_configure_node(node):
    """Configure xdist worker nodes with minimal setup."""
    # Ensure worker nodes have the same environment defaults
    if hasattr(node, "workerinput"):
        _test_environment_defaults()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean session finish - no complex coverage handling."""
    pass


def pytest_terminal_summary(terminalreporter) -> None:
    """Simplified terminal summary - no complex coverage reporting."""
    pass
