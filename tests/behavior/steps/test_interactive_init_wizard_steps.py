from __future__ import annotations

import os
import json
import toml
import yaml
from devsynth.config.unified_loader import UnifiedConfigLoader
from pathlib import Path
from typing import Sequence, Optional
from unittest.mock import MagicMock

import pytest
from pytest_bdd import scenarios, given, when, then

from devsynth.interface.ux_bridge import UXBridge


class DummyBridge(UXBridge):
    def __init__(self, answers: Sequence[str], confirms: Sequence[bool]):
        self.answers = list(answers)
        self.confirms = list(confirms)

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        return self.answers.pop(0)

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return self.confirms.pop(0)

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        pass


scenarios("../features/general/interactive_init_wizard.feature")


@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@when("I run the initialization wizard")
def run_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(os.sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(os.sys.modules, "uvicorn", MagicMock())
    from devsynth.application.cli.cli_commands import init_cmd

    answers = [
        str(tmp_project_dir),
        "python",
        "demo goals",
        "kuzu",
    ]
    confirms = [
        True,  # offline mode
        True,  # wsde_collaboration
        False,  # dialectical_reasoning
        False,  # code_generation
        False,  # test_generation
        False,  # documentation_generation
        False,  # experimental_features
        True,  # proceed
    ]
    bridge = DummyBridge(answers, confirms)
    # Pass an empty features dict so the wizard prompts for each feature
    # allowing our ``DummyBridge`` confirmations to be used.
    init_cmd(bridge=bridge, features={})


@then("a project configuration file should include the selected options")
def check_config(tmp_project_dir):
    cfg = UnifiedConfigLoader.load(tmp_project_dir).config
    assert cfg.memory_store_type == "kuzu"
    assert cfg.offline_mode is True
    assert cfg.features["wsde_collaboration"] is True
