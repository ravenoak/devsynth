"""Steps for the config_enable_feature.feature."""

import os
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.config.loader import ConfigModel, load_config, save_config
from tests.behavior.feature_paths import feature_path

from .cli_commands_steps import *

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "config_enable_feature.feature"))


@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.root = None
            self.cfg_path = None
            self.orig_cwd = None
            self.monkeypatch = None

    return Context()


@given('a project configuration without the "code_generation" feature enabled')
def config_without_feature(tmp_path, monkeypatch, context):
    cfg = ConfigModel(project_root=str(tmp_path))
    cfg.features["code_generation"] = False
    context.cfg_path = save_config(cfg, path=str(tmp_path))
    context.root = tmp_path
    context.orig_cwd = Path(os.environ.get("ORIGINAL_CWD", Path.cwd()))
    context.monkeypatch = monkeypatch
    assert context.cfg_path.exists()
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
def feature_enabled(context):
    cfg = load_config()
    assert cfg.project_root == str(context.root)
    assert cfg.features.get("code_generation") is True
    assert context.cfg_path.exists()
    monkeypatch = context.monkeypatch
    if monkeypatch:
        monkeypatch.chdir(context.orig_cwd)
        monkeypatch._cwd = context.orig_cwd  # ensure undo path exists
    else:
        os.chdir(context.orig_cwd)
