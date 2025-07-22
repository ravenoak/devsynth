import os
import json
import sys
from typing import Sequence, Optional
from unittest.mock import MagicMock

import pytest
from pytest_bdd import scenarios, given, when, then

from devsynth.interface.ux_bridge import UXBridge


class DummyBridge(UXBridge):
    def __init__(self, answers: Sequence[str]):
        self.answers = list(answers)
        self.index = 0

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        response = self.answers[self.index]
        self.index += 1
        return response

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return True

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        pass


scenarios("../features/general/interactive_requirements.feature")


@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@when("I run the interactive requirements wizard")
def run_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())
    from devsynth.application.cli.requirements_commands import wizard_cmd

    answers = [
        "Sample title",
        "Sample description",
        "functional",
        "medium",
        "",
    ]
    bridge = DummyBridge(answers)
    output = os.path.join(tmp_project_dir, "requirements_wizard.json")
    wizard_cmd(output_file=output, bridge=bridge)


@then('a structured requirements file "requirements_wizard.json" should exist')
def check_file(tmp_project_dir):
    path = os.path.join(tmp_project_dir, "requirements_wizard.json")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("title") == "Sample title"
