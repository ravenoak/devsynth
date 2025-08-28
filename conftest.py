"""Root conftest.py to ensure pytest-bdd configuration is properly loaded.

Also gates coverage thresholds via environment variables so that strict coverage
is only enforced on full-suite jobs.

Env vars:
- DEVSYNTH_FULL_COVERAGE=1 or DEVSYNTH_STRICT_COVERAGE=1 -> enforce strict coverage
- DEVSYNTH_COV_FAIL_UNDER=<int> -> override coverage fail-under threshold
"""

import importlib.util
import os
from typing import Dict, Iterator

import pytest


def _setup_pytest_bdd() -> None:
    """Configure pytest-bdd if the plugin is available."""
    try:
        spec = importlib.util.find_spec("pytest_bdd.utils")
    except ModuleNotFoundError:
        spec = None
    if spec is None:
        return

    from pytest_bdd.utils import CONFIG_STACK  # local import

    @pytest.hookimpl(trylast=True)
    def pytest_configure(config):
        """Configure pytest-bdd and register custom markers."""
        config.addinivalue_line(
            "markers",
            "isolation: mark test to run in isolation due to interactions with other tests",
        )

        if not CONFIG_STACK:
            CONFIG_STACK.append(config)

        features_dir = os.path.join(
            os.path.dirname(__file__),
            "tests",
            "behavior",
            "features",
        )
        config.option.bdd_features_base_dir = features_dir
        config._inicache["bdd_features_base_dir"] = features_dir


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Gate coverage enforcement via environment variables and register gui marker.

    By default (no env var set), disable coverage fail-under to keep fast CI runs green.
    When DEVSYNTH_FULL_COVERAGE or DEVSYNTH_STRICT_COVERAGE is set, allow an override
    threshold via DEVSYNTH_COV_FAIL_UNDER; otherwise keep whatever CLI/ini configured.
    """
    # Always ensure the gui marker is registered, even if ini misses it.
    config.addinivalue_line(
        "markers",
        "gui: mark test as requiring GUI or optional UI extras (NiceGUI/DearPyGUI)",
    )

    strict = os.getenv("DEVSYNTH_FULL_COVERAGE") or os.getenv(
        "DEVSYNTH_STRICT_COVERAGE"
    )
    cov_fail_under_env = os.getenv("DEVSYNTH_COV_FAIL_UNDER")

    # Only adjust if pytest-cov is active and option present
    if hasattr(config, "option") and hasattr(config.option, "cov_fail_under"):
        if not strict:
            # Relax coverage enforcement for default/fast runs
            try:
                config.option.cov_fail_under = (
                    0  # do not fail builds on coverage by default
                )
            except Exception:
                pass
        else:
            # Enforce strict coverage with optional override
            if cov_fail_under_env:
                try:
                    config.option.cov_fail_under = int(cov_fail_under_env)
                except ValueError:
                    # Ignore bad value; keep existing threshold
                    pass


# --- Test isolation and defaults -------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _devsynth_test_env_defaults() -> None:
    """Set conservative, offline-first defaults for tests.

    Tests can override these via monkeypatch.setenv within individual test functions.
    We only set values if they are not already present in the environment to respect
    explicit user/CI configuration.
    """
    os.environ.setdefault("DEVSYNTH_OFFLINE", "true")
    os.environ.setdefault("DEVSYNTH_PROVIDER", "stub")

    # Resource availability defaults (skip heavy/remote by default)
    os.environ.setdefault("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false")
    os.environ.setdefault("DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE", "true")
    os.environ.setdefault("DEVSYNTH_RESOURCE_CLI_AVAILABLE", "true")

    # Safe defaults for provider endpoints/keys used by stubs
    os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
    os.environ.setdefault("LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234")


@pytest.fixture(autouse=True)
def _restore_env_and_cwd_between_tests() -> Iterator[None]:
    """Snapshot and restore os.environ and the current working directory per test.

    - Captures a shallow copy of os.environ and the current working directory.
    - Yields to the test, allowing it to mutate env and chdir as needed.
    - Restores both environment variables and CWD to the captured state.

    Note: Prefer using pytest's monkeypatch fixture in tests for clarity; this
    fixture guarantees restoration even if monkeypatch isn't used.
    """
    # Snapshot environment and cwd
    env_before: Dict[str, str] = dict(os.environ)
    cwd_before = os.getcwd()
    try:
        yield
    finally:
        # Restore environment completely
        os.environ.clear()
        os.environ.update(env_before)
        # Restore working directory if changed
        try:
            os.chdir(cwd_before)
        except Exception:
            # If the directory no longer exists, fallback to repo root
            repo_root = os.path.dirname(__file__)
            os.chdir(repo_root)


_setup_pytest_bdd()
