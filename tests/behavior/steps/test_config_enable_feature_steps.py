"""Steps for the config_enable_feature.feature."""

import os
from pathlib import Path

from pytest_bdd import given, scenarios, when, then

from devsynth.config.loader import ConfigModel, save_config, load_config
from .cli_commands_steps import run_command

scenarios("../features/config_enable_feature.feature")


@given('a project configuration without the "code_generation" feature enabled')
def config_without_feature(tmp_path, monkeypatch):
    cfg = ConfigModel(project_root=str(tmp_path))
    cfg.features["code_generation"] = False
    save_config(cfg, path=str(tmp_path))
    monkeypatch.chdir(tmp_path)


@when('I run the command "devsynth config enable-feature code_generation"')
def enable_feature(monkeypatch, mock_workflow_manager, command_context):
    return run_command(
        "devsynth config enable-feature code_generation",
        monkeypatch,
        mock_workflow_manager,
        command_context,
    )


@then('the configuration should mark "code_generation" as enabled')
def feature_enabled():
    cfg = load_config()
    assert cfg.features.get("code_generation") is True
