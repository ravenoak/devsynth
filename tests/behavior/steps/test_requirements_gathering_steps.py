import os
import sys
from types import ModuleType
from typing import Optional, Sequence
from unittest.mock import MagicMock

import pytest
import yaml
from pytest_bdd import given, scenarios, then, when

from devsynth.interface.ux_bridge import UXBridge

from .webui_steps import webui_context

pytest_plugins = ["tests.fixtures.webui_test_utils"]


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


scenarios("../features/general/requirements_gathering.feature")


@pytest.mark.medium
@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@pytest.mark.medium
@when("I run the requirements gathering wizard")
def run_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())
    from devsynth.application.cli.cli_commands import gather_cmd

    answers = [
        "Goal one,Goal two",
        "Constraint A,Constraint B",
        "high",
    ]
    bridge = DummyBridge(answers)
    output = os.path.join(tmp_project_dir, "requirements_plan.yaml")
    os.chdir(tmp_project_dir)
    gather_cmd(output_file=output, bridge=bridge)


@pytest.mark.medium
@given("the WebUI is initialized")
def given_webui_initialized(webui_context):
    return webui_context


@pytest.mark.medium
@when("I run the requirements gathering wizard in the WebUI")
def run_webui_wizard(tmp_project_dir, webui_context):
    webui_context["st"].sidebar.radio.return_value = "Requirements"
    answers = iter(
        [
            "Goal one,Goal two",
            "Constraint A,Constraint B",
            "high",
        ]
    )
    webui_context["ui"].ask_question = lambda *a, **k: next(answers)
    webui_context["ui"].confirm = lambda *a, **k: True
    with open(
        os.path.join(tmp_project_dir, "pyproject.toml"), "w", encoding="utf-8"
    ) as f:
        f.write("[tool.devsynth]\n")
    output = os.path.join(tmp_project_dir, "requirements_plan.yaml")
    os.chdir(tmp_project_dir)
    from devsynth.application.requirements.interactions import gather_requirements

    gather_requirements(webui_context["ui"], output_file=output)


@pytest.mark.medium
@then('a requirements plan file "requirements_plan.yaml" should exist')
def check_file(tmp_project_dir):
    path = os.path.join(tmp_project_dir, "requirements_plan.yaml")
    assert os.path.exists(path)
    data = yaml.safe_load(open(path))
    assert data.get("priority") == "high"
    assert data.get("goals") == ["Goal one", "Goal two"]
    assert data.get("constraints") == ["Constraint A", "Constraint B"]
