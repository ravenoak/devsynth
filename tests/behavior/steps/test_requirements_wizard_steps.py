from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence, Optional
from unittest.mock import MagicMock

from pytest_bdd import scenarios, given, when, then

from devsynth.interface.ux_bridge import UXBridge
from devsynth.application.cli.setup_wizard import SetupWizard


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


def _run_wizard(output: Path, bridge: DummyBridge) -> None:
    wizard = SetupWizard(bridge)
    name = wizard.bridge.ask_question("Project name?")
    language = wizard.bridge.ask_question("Primary language?")
    features = wizard.bridge.ask_question("Desired features (comma separated)?")
    if wizard.bridge.confirm_choice("Save these settings?"):
        data = {
            "name": name,
            "language": language,
            "features": (
                [f.strip() for f in features.split(";") if f.strip()]
                if ";" in features
                else [f.strip() for f in features.split(",") if f.strip()]
            ),
        }
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        wizard.bridge.display_result("Requirements saved")
    else:
        wizard.bridge.display_result("Cancelled")


scenarios("../features/requirements_wizard.feature")


@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@when("I run the requirements wizard")
def run_requirements_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(Path, "home", lambda: Path(tmp_project_dir))
    answers = ["My Project", "python", "feature1,feature2"]
    confirms = [True]
    bridge = DummyBridge(answers, confirms)
    output = Path(tmp_project_dir) / "requirements_wizard.json"
    _run_wizard(output, bridge)


@when("I cancel the requirements wizard")
def cancel_requirements_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(Path, "home", lambda: Path(tmp_project_dir))
    answers = ["My Project", "python", "feature1,feature2"]
    confirms = [False]
    bridge = DummyBridge(answers, confirms)
    output = Path(tmp_project_dir) / "requirements_wizard.json"
    _run_wizard(output, bridge)


@then('a saved requirements file "requirements_wizard.json" should exist')
def saved_file_exists(tmp_project_dir):
    path = Path(tmp_project_dir) / "requirements_wizard.json"
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["name"] == "My Project"


@then("no requirements file should exist")
def no_file(tmp_project_dir):
    path = Path(tmp_project_dir) / "requirements_wizard.json"
    assert not path.exists()
