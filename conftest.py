"""Root conftest.py to ensure pytest-bdd configuration is properly loaded.

Also gates coverage thresholds via environment variables so that strict coverage
is only enforced on full-suite jobs.

## API Key and Testing Constraints

### LLM Provider Testing Requirements

**Anthropic API**: Currently waiting on valid API key for testing. Tests requiring Anthropic API are expected to fail until key is available.

**OpenAI API**: Valid API keys available. Use only cheap, inexpensive models (e.g., gpt-3.5-turbo, gpt-4o-mini) and only when absolutely necessary for testing core functionality.

**OpenRouter API**: Valid API keys available with free-tier access. Use OpenRouter free-tier for:
- All OpenRouter-specific tests
- General tests requiring live LLM functionality
- Prefer OpenRouter over OpenAI for cost efficiency

**LM Studio**: Tests run on same host as application tests. Resources are limited - use large timeouts (60+ seconds) and consider resource constraints when designing tests.

### Environment Variables for LLM Testing

Set the following environment variables for LLM provider testing:

```bash
# OpenRouter (preferred for testing)
export OPENROUTER_API_KEY="your-openrouter-key"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

# OpenAI (use sparingly, only cheap models)
export OPENAI_API_KEY="your-openai-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"

# LM Studio (local testing)
export LM_STUDIO_ENDPOINT="http://127.0.0.1:1234"
export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE="true"
```

Env vars:
- DEVSYNTH_FULL_COVERAGE=1 or DEVSYNTH_STRICT_COVERAGE=1 -> enforce strict coverage
- DEVSYNTH_COV_FAIL_UNDER=<int> -> override coverage fail-under threshold
"""

import importlib.util
import os
import sys
import time
from pathlib import Path
from typing import Dict, Iterator, List, Optional

import pytest


def _should_load_bdd() -> bool:
    """Check if BDD should be loaded based on command line arguments."""
    import sys

    return any("behavior" in arg for arg in sys.argv)


def _setup_pytest_bdd() -> None:
    """Configure pytest-bdd if the plugin is available."""
    # Skip BDD setup entirely if not running behavior tests
    if not _should_load_bdd():
        return

    try:
        spec = importlib.util.find_spec("pytest_bdd.utils")
    except ModuleNotFoundError:
        spec = None
    if spec is None:
        return

    from pytest_bdd.utils import CONFIG_STACK  # local import

    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(config):
        """Configure pytest-bdd and register custom markers."""
        # Only configure BDD if behavior tests are being run
        if not any("behavior" in str(arg) for arg in config.args):
            return

        config.addinivalue_line(
            "markers",
            "isolation: mark test to run in isolation due to interactions with other tests",
        )

        if not CONFIG_STACK:
            CONFIG_STACK.append(config)

        # Optimize BDD features directory for faster discovery
        features_dir = os.path.join(
            os.path.dirname(__file__),
            "tests",
            "behavior",
            "features",
        )
        config.option.bdd_features_base_dir = features_dir
        config._inicache["bdd_features_base_dir"] = features_dir

        # Optimize BDD scenario loading
        config.option.bdd_strict_markers = False  # Reduce marker validation overhead
        config.option.bdd_dry_run = False  # Skip dry run for faster collection


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

    # Only adjust coverage for non-smoke, non-collection runs to improve performance
    if config.getoption("--collect-only") or config.getoption(
        "-m", default=""
    ).startswith("smoke"):
        # Disable coverage for collection-only and smoke runs
        try:
            config.option.cov_fail_under = 0
        except Exception:
            pass
    elif hasattr(config, "option") and hasattr(config.option, "cov_fail_under"):
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

    cov_source = getattr(getattr(config, "option", None), "cov_source", None)
    if cov_source:
        try:
            sources = list(cov_source)
        except TypeError:
            sources = [cov_source]

        if "src/devsynth" in sources:
            specific_sources = [
                source for source in sources if source != "src/devsynth"
            ]
            if specific_sources:
                config.option.cov_source = specific_sources
                sources = specific_sources

        # Simplified coverage configuration - use standard .coveragerc for all cases
        # Remove complex WebUI-specific coverage patching in favor of unified configuration


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


def pytest_sessionfinish(
    session: pytest.Session, exitstatus: int
) -> None:  # noqa: ARG001
    """Session cleanup - simplified from complex WebUI coverage handling."""
    pass


@pytest.hookimpl(tryfirst=True)
def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Terminal summary - simplified from complex coverage handling."""
    pass


_setup_pytest_bdd()


# Simplified coverage handling - removed complex WebUI-specific coverage patching
# All coverage configuration now handled through unified .coveragerc


# Collection optimization to improve performance
_collection_cache: Optional[Dict[str, List[str]]] = None
_cache_timestamp: Optional[float] = None
_CACHE_TTL = 300  # 5 minutes


def _should_use_cache() -> bool:
    """Check if we should use cached collection results."""
    if _collection_cache is None or _cache_timestamp is None:
        return False
    return (time.time() - _cache_timestamp) < _CACHE_TTL


def _get_cache_key(config: pytest.Config) -> str:
    """Generate a cache key based on pytest configuration."""
    # Include relevant config options that affect collection
    key_parts = [
        str(config.getoption("--collect-only", default=False)),
        str(config.getoption("-m", default="")),
        str(config.getoption("-k", default="")),
        str(config.getoption("--maxfail", default=0)),
    ]
    return "|".join(key_parts)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item]
) -> None:
    """Optimize test collection by deferring expensive marker evaluation.

    This hook runs after test collection but before test execution,
    allowing us to optimize marker filtering and other expensive operations.
    """
    # Skip optimization during collection-only runs
    if config.getoption("--collect-only"):
        return

    # For smoke runs, be more aggressive about filtering to improve performance
    marker_expr = config.getoption("-m", default="")
    if marker_expr.startswith("smoke") or marker_expr == "smoke":
        # For smoke runs, only include fast tests to dramatically improve performance
        fast_items = []
        for item in items:
            # Check if item has fast marker or no speed marker (assume fast)
            has_fast_marker = False
            has_slow_marker = False

            for marker in item.iter_markers():
                if marker.name == "fast":
                    has_fast_marker = True
                elif marker.name == "slow":
                    has_slow_marker = True

            # Include item if it's fast or has no speed marker (assume fast)
            if has_fast_marker or not has_slow_marker:
                fast_items.append(item)

        # Replace items with filtered list for much faster execution
        items[:] = fast_items
