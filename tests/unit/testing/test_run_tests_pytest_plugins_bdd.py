import os

import pytest

from devsynth.testing import run_tests as run_tests_module


@pytest.mark.fast
def test_ensure_pytest_bdd_plugin_env_adds_plugin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: PYTEST-BDD-01 — Inject plugin when autoloading is disabled."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    env = os.environ
    changed = run_tests_module.ensure_pytest_bdd_plugin_env(env)

    assert changed is True
    assert env.get("PYTEST_ADDOPTS") == "-p pytest_bdd.plugin"


@pytest.mark.fast
def test_ensure_pytest_bdd_plugin_env_requires_autoload_disable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: PYTEST-BDD-02 — Early exit when autoload remains enabled."""

    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k bdd")

    env = os.environ
    changed = run_tests_module.ensure_pytest_bdd_plugin_env(env)

    assert changed is False
    assert env.get("PYTEST_ADDOPTS") == "-k bdd"


@pytest.mark.fast
def test_ensure_pytest_bdd_plugin_env_detects_existing_plugin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: PYTEST-BDD-03 — Respect existing '-p pytest_bdd.plugin' tokens."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", " -ppytest_bdd.plugin   -k slow ")

    env = os.environ
    changed = run_tests_module.ensure_pytest_bdd_plugin_env(env)

    assert changed is False
    assert env.get("PYTEST_ADDOPTS") == " -ppytest_bdd.plugin   -k slow "


@pytest.mark.fast
def test_ensure_pytest_bdd_plugin_env_respects_explicit_disable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: PYTEST-BDD-04 — Honor '-p no:pytest_bdd' overrides."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "-p no:pytest_bdd -s")

    env = os.environ
    changed = run_tests_module.ensure_pytest_bdd_plugin_env(env)

    assert changed is False
    assert env.get("PYTEST_ADDOPTS") == "-p no:pytest_bdd -s"


@pytest.mark.fast
@pytest.mark.parametrize(
    ("addopts", "expected_changed", "expected_addopts"),
    (
        ("-p no:pytest_bdd -s", False, "-p no:pytest_bdd -s"),
        ("-k feature", True, "-k feature -p pytest_bdd.plugin"),
    ),
)
def test_ensure_pytest_bdd_plugin_env_handles_explicit_optouts(
    monkeypatch: pytest.MonkeyPatch,
    addopts: str,
    expected_changed: bool,
    expected_addopts: str,
) -> None:
    """Parameterize pytest-bdd opt-out and reinjection flows."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", addopts)

    env = os.environ
    changed = run_tests_module.ensure_pytest_bdd_plugin_env(env)

    assert changed is expected_changed
    assert env.get("PYTEST_ADDOPTS") == expected_addopts


@pytest.mark.fast
def test_pytest_plugins_registers_pytest_bdd_once() -> None:
    """Ensure the centralized helper exports pytest-bdd exactly once."""

    import importlib

    registry = importlib.import_module("tests.pytest_plugin_registry")
    plugin_list = list(registry.PYTEST_PLUGINS)

    assert plugin_list.count("pytest_bdd.plugin") == 1

    root_conftest = importlib.import_module("tests.conftest")
    assert "pytest_bdd.plugin" in root_conftest.pytest_plugins
    assert "tests.behavior.steps._pytest_bdd_proxy" not in root_conftest.pytest_plugins
