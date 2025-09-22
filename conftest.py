"""Root conftest.py to ensure pytest-bdd configuration is properly loaded.

Also gates coverage thresholds via environment variables so that strict coverage
is only enforced on full-suite jobs.

Env vars:
- DEVSYNTH_FULL_COVERAGE=1 or DEVSYNTH_STRICT_COVERAGE=1 -> enforce strict coverage
- DEVSYNTH_COV_FAIL_UNDER=<int> -> override coverage fail-under threshold
"""

import importlib.util
import os
import sys
from pathlib import Path
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

    cov_source = getattr(getattr(config, "option", None), "cov_source", None)
    if cov_source:
        try:
            sources = list(cov_source)
        except TypeError:
            sources = [cov_source]

        if "src/devsynth" in sources:
            specific_sources = [source for source in sources if source != "src/devsynth"]
            if specific_sources:
                config.option.cov_source = specific_sources
                sources = specific_sources

        if any(source == "devsynth.interface.webui" for source in sources):
            repo_root = Path(__file__).resolve().parent
            target_file = repo_root / "src" / "devsynth" / "interface" / "webui.py"
            config.option.cov_source = None
            config.option.cov_config = str(repo_root / "tests" / "coverage_webui_only.rc")

            try:
                import coverage as coverage_mod  # type: ignore[import-not-found]
            except Exception:  # pragma: no cover - coverage module should be present when --cov is used
                coverage_mod = None
            else:
                if not hasattr(coverage_mod, "_devsynth_webui_patch"):
                    original_coverage = coverage_mod.Coverage

                    def _webui_only_coverage(*args, **kwargs):
                        params = dict(kwargs)
                        params["source"] = [str(target_file)]

                        include = params.get("include")
                        if include is None:
                            include_list: list[str] = []
                        else:
                            include_list = list(include)
                        file_path = str(target_file)
                        if file_path not in include_list:
                            include_list.append(file_path)
                        params["include"] = include_list

                        omit = params.get("omit")
                        if omit is None:
                            omit_list: list[str] = []
                        else:
                            omit_list = list(omit)
                        omit_pattern = str(target_file.parent / "*")
                        if omit_pattern not in omit_list:
                            omit_list.append(omit_pattern)
                        params["omit"] = omit_list

                        instance = original_coverage(*args, **params)
                        tracked = getattr(
                            coverage_mod, "_devsynth_webui_instances", []
                        )
                        tracked.append(instance)
                        coverage_mod._devsynth_webui_instances = tracked  # type: ignore[attr-defined]
                        return instance

                    coverage_mod._devsynth_webui_patch = original_coverage  # type: ignore[attr-defined]
                    coverage_mod.Coverage = _webui_only_coverage  # type: ignore[assignment]

            config._devsynth_webui_cov_target = True  # type: ignore[attr-defined]

            cov_plugin = None
            for plugin in config.pluginmanager.get_plugins():
                if plugin.__class__.__name__ == "CovPlugin":
                    cov_plugin = plugin
                    break
            if cov_plugin and not hasattr(cov_plugin, "_devsynth_webui_patched"):
                original_summary = cov_plugin.pytest_terminal_summary

                def _patched_terminal_summary(terminalreporter, exitstatus):
                    controller = getattr(cov_plugin, "cov_controller", None)
                    if controller is not None:
                        _prune_cov_object(getattr(controller, "cov", None))
                        _prune_cov_object(getattr(controller, "combining_cov", None))
                    return original_summary(terminalreporter, exitstatus)

                cov_plugin.pytest_terminal_summary = _patched_terminal_summary  # type: ignore[assignment]
                cov_plugin._devsynth_webui_patched = True  # type: ignore[attr-defined]

            include = getattr(config.option, "cov_include", None)
            if not include:
                include_list: list[str] = []
            else:
                include_list = list(include)
            include_pattern = str(target_file)
            if include_pattern not in include_list:
                include_list.append(include_pattern)
            config.option.cov_include = include_list

            omit = getattr(config.option, "cov_omit", None)
            if not omit:
                omit_list = []
            else:
                omit_list = list(omit)
            omit_pattern = str(target_file.parent / "*")
            if omit_pattern not in omit_list:
                omit_list.append(omit_pattern)
            config.option.cov_omit = omit_list


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


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:  # noqa: ARG001
    """Prune coverage data to the WebUI module when targeting focused runs."""

    if not getattr(session.config, "_devsynth_webui_cov_target", False):
        return

    _prune_webui_coverage_data()


@pytest.hookimpl(tryfirst=True)
def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Ensure coverage pruning runs before pytest-cov prints its report."""

    if getattr(terminalreporter.config, "_devsynth_webui_cov_target", False):
        _prune_webui_coverage_data()


_setup_pytest_bdd()


def _prune_webui_coverage_data() -> None:
    """Remove non-WebUI files from coverage data for focused runs."""

    try:
        import coverage  # type: ignore[import-not-found]
    except Exception:  # pragma: no cover - coverage module should be available with --cov
        return

    cov = coverage.Coverage()
    try:
        cov.load()
    except Exception:  # pragma: no cover - if no data yet, skip pruning
        return

    target_file = Path(__file__).resolve().parent / "src" / "devsynth" / "interface" / "webui.py"
    data = cov.get_data()
    for filename in list(data.measured_files()):
        if Path(filename) != target_file:
            data.erase(filename)
    cov.save()


def _prune_cov_object(cov_obj) -> None:
    """Trim measured files on a coverage object in-memory."""

    if cov_obj is None:
        return

    target_file = Path(__file__).resolve().parent / "src" / "devsynth" / "interface" / "webui.py"
    try:
        data = cov_obj.get_data()
    except Exception:  # pragma: no cover - guard for coverage internals
        return
    for filename in list(data.measured_files()):
        if Path(filename) != target_file:
            data.erase(filename)
if any("--cov=devsynth.interface.webui" in arg for arg in sys.argv):
    repo_root = Path(__file__).resolve().parent
    os.environ["COVERAGE_RCFILE"] = str(repo_root / "tests" / "coverage_webui_only.rc")

