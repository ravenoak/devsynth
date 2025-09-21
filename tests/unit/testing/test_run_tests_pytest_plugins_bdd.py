import os

import pytest

from devsynth.testing import run_tests as run_tests_module


@pytest.mark.fast
def test_ensure_pytest_bdd_plugin_env_adds_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
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
