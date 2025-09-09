import logging
import os

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app


@pytest.fixture(autouse=True)
def _restore_logging_state():
    # Save and restore root logger level to avoid cross-test interference
    root = logging.getLogger()
    prev_level = root.level
    yield
    root.setLevel(prev_level)


@pytest.mark.fast
def test_global_debug_flag_sets_log_level_debug(monkeypatch):
    runner = CliRunner()
    # Ensure env does not force level
    monkeypatch.delenv("DEVSYNTH_LOG_LEVEL", raising=False)
    monkeypatch.delenv("DEVSYNTH_DEBUG", raising=False)

    app = build_app()
    result = runner.invoke(app, ["--debug", "--version"])  # triggers callback and exit
    assert result.exit_code == 0
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG
    assert os.environ.get("DEVSYNTH_LOG_LEVEL") == "DEBUG"


@pytest.mark.fast
def test_env_debug_sets_log_level_when_no_flag(monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("DEVSYNTH_DEBUG", "1")
    monkeypatch.delenv("DEVSYNTH_LOG_LEVEL", raising=False)

    app = build_app()
    result = runner.invoke(app, ["--version"])  # triggers callback
    assert result.exit_code == 0
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG
    assert os.environ.get("DEVSYNTH_LOG_LEVEL") == "DEBUG"


@pytest.mark.fast
def test_log_level_option_overrides_env_debug(monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("DEVSYNTH_DEBUG", "true")
    monkeypatch.delenv("DEVSYNTH_LOG_LEVEL", raising=False)

    app = build_app()
    result = runner.invoke(app, ["--log-level", "WARNING", "--version"])  # eager
    assert result.exit_code == 0
    assert logging.getLogger().getEffectiveLevel() == logging.WARNING
    assert os.environ.get("DEVSYNTH_LOG_LEVEL") == "WARNING"
