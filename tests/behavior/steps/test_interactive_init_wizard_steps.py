from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import toml
import yaml
from pytest_bdd import given, scenarios, then, when

from devsynth.config.unified_loader import UnifiedConfigLoader
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "interactive_init_wizard.feature"))


@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@when("I run the initialization wizard")
def run_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(os.sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(os.sys.modules, "uvicorn", MagicMock())
    from devsynth.application.cli.cli_commands import init_cmd

    monkeypatch.setenv("DEVSYNTH_INIT_ROOT", str(tmp_project_dir))
    monkeypatch.setenv("DEVSYNTH_INIT_LANGUAGE", "python")
    monkeypatch.setenv("DEVSYNTH_INIT_GOALS", "demo goals")
    monkeypatch.setenv("DEVSYNTH_INIT_MEMORY_BACKEND", "kuzu")
    monkeypatch.setenv("DEVSYNTH_INIT_OFFLINE_MODE", "1")
    monkeypatch.setenv("DEVSYNTH_INIT_FEATURES", "wsde_collaboration")
    init_cmd(auto_confirm=True)


@then("a project configuration file should include the selected options")
def check_config(tmp_project_dir):
    cfg = UnifiedConfigLoader.load(tmp_project_dir).config
    assert cfg.memory_store_type == "kuzu"
    assert cfg.offline_mode is True
    assert cfg.features["wsde_collaboration"] is True
