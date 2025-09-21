import os

import pytest

from devsynth.testing import run_tests as run_tests_module


@pytest.mark.fast
def test_ensure_pytest_cov_plugin_env_adds_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto-loading disabled requires explicit pytest-cov plugin injection."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    env = os.environ
    changed = run_tests_module.ensure_pytest_cov_plugin_env(env)

    assert changed is True
    assert env.get("PYTEST_ADDOPTS") == "-p pytest_cov"


@pytest.mark.fast
def test_ensure_pytest_cov_plugin_env_requires_autoload_disable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: PYTEST-COV-03 — No injection when plugin autoload remains enabled."""

    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k fast")

    env = os.environ
    changed = run_tests_module.ensure_pytest_cov_plugin_env(env)

    assert changed is False
    assert env.get("PYTEST_ADDOPTS") == "-k fast"


@pytest.mark.fast
def test_ensure_pytest_cov_plugin_env_respects_explicit_disables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit --no-cov and -p overrides keep pytest-cov disabled."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--no-cov -p no:pytest_cov")

    env = os.environ
    changed = run_tests_module.ensure_pytest_cov_plugin_env(env)

    assert changed is False
    assert env.get("PYTEST_ADDOPTS") == "--no-cov -p no:pytest_cov"


@pytest.mark.fast
def test_ensure_pytest_cov_plugin_env_detects_inline_plugin_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: PYTEST-COV-02 — '-ppytest_cov' tokens keep configuration stable."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", " -ppytest_cov   -k fast ")

    env = os.environ
    changed = run_tests_module.ensure_pytest_cov_plugin_env(env)

    assert changed is False
    assert env.get("PYTEST_ADDOPTS") == " -ppytest_cov   -k fast "
