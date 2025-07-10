from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence, Optional
from unittest.mock import MagicMock

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


scenarios("../features/setup_wizard.feature")


@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@when("I run the setup wizard")
def run_setup_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(os.sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(os.sys.modules, "uvicorn", MagicMock())
    from devsynth.application.cli.setup_wizard import SetupWizard

    answers = [
        str(tmp_project_dir),
        "single_package",
        "python",
        "",
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
    wizard = SetupWizard(bridge)
    wizard.run()


@when("I cancel the setup wizard")
def cancel_setup_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(os.sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(os.sys.modules, "uvicorn", MagicMock())
    from devsynth.application.cli.setup_wizard import SetupWizard

    answers = [
        str(tmp_project_dir),
        "single_package",
        "python",
        "",
        "",
        "memory",
    ]
    confirms = [
        False,  # offline mode
        False,  # wsde_collaboration
        False,  # dialectical_reasoning
        False,  # code_generation
        False,  # test_generation
        False,  # documentation_generation
        False,  # experimental_features
        False,  # proceed
    ]
    bridge = DummyBridge(answers, confirms)
    wizard = SetupWizard(bridge)
    wizard.run()


@then("a project configuration file should include the selected options")
def check_config(tmp_project_dir):
    from devsynth.config.unified_loader import UnifiedConfigLoader

    cfg = UnifiedConfigLoader.load(tmp_project_dir).config
    assert cfg.memory_store_type == "kuzu"
    assert cfg.offline_mode is True
    assert cfg.features["wsde_collaboration"] is True


@then("no project configuration file should exist")
def no_config(tmp_project_dir):
    cfg_file = Path(tmp_project_dir) / ".devsynth" / "project.yaml"
    assert not cfg_file.exists()
