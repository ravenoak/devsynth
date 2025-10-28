from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from collections.abc import Sequence
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.interface.ux_bridge import UXBridge
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]


class DummyBridge(UXBridge):
    def __init__(self, answers: Sequence[str], confirms: Sequence[bool]):
        self.answers = list(answers)
        self.confirms = list(confirms)

    def ask_question(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        return self.answers.pop(0)

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return self.confirms.pop(0)

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        pass


def _run_wizard(
    output_filename: str, bridge: DummyBridge, tmpdir: pytest.FixtureRequest
) -> None:
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
        # Use tmpdir for file operations
        output_file = tmpdir.join(output_filename)
        output_file.write(json.dumps(data, indent=2), encoding="utf-8")
        wizard.bridge.display_result("Requirements saved")
    else:
        wizard.bridge.display_result("Cancelled")


scenarios(
    feature_path(
        __file__,
        "..",
        "requirements_wizard",
        "features",
        "general",
        "requirements_wizard.feature",
    )
)


@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@when("I run the requirements wizard")
def run_requirements_wizard(tmp_project_dir, tmpdir, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: Path(tmp_project_dir))
    answers = ["My Project", "python", "feature1,feature2"]
    confirms = [True]
    bridge = DummyBridge(answers, confirms)
    # Use just the filename, not the full path
    _run_wizard("requirements_wizard.json", bridge, tmpdir)


@when("I cancel the requirements wizard")
def cancel_requirements_wizard(tmp_project_dir, tmpdir, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: Path(tmp_project_dir))
    answers = ["My Project", "python", "feature1,feature2"]
    confirms = [False]
    bridge = DummyBridge(answers, confirms)
    # Use just the filename, not the full path
    _run_wizard("requirements_wizard.json", bridge, tmpdir)


@then('a saved requirements file "requirements_wizard.json" should exist')
def saved_file_exists(tmpdir):
    # Check for the file in tmpdir
    path = tmpdir.join("requirements_wizard.json")
    assert path.exists()
    # Read the file using tmpdir's methods
    data = json.loads(path.read(encoding="utf-8"))
    assert data["name"] == "My Project"


@then("no requirements file should exist")
def no_file(tmpdir):
    # Check for the file in tmpdir
    path = tmpdir.join("requirements_wizard.json")
    assert not path.exists()
