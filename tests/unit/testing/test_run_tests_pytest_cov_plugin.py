import os

import pytest

from devsynth.testing import run_tests as run_tests_module


@pytest.mark.fast
def test_ensure_pytest_cov_plugin_env_adds_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto-loading disabled requires explicit pytest-cov plugin injection."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    changed = run_tests_module.ensure_pytest_cov_plugin_env(os.environ)

    assert changed is True
    assert os.environ.get("PYTEST_ADDOPTS") == "-p pytest_cov"


@pytest.mark.fast
def test_ensure_pytest_cov_plugin_env_respects_explicit_disables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit --no-cov and -p overrides keep pytest-cov disabled."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--no-cov -p no:pytest_cov")

    changed = run_tests_module.ensure_pytest_cov_plugin_env(os.environ)

    assert changed is False
    assert os.environ.get("PYTEST_ADDOPTS") == "--no-cov -p no:pytest_cov"
