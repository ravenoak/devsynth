import json
import os
import sys
from typing import Optional
from collections.abc import Sequence
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.requirements.interactions import RequirementsCollector
from devsynth.interface.ux_bridge import UXBridge
from tests.behavior.feature_paths import feature_path

from .webui_steps import webui_context

pytestmark = [pytest.mark.fast]


class DummyBridge(UXBridge):
    def __init__(self, answers: Sequence[str]):
        self.answers = list(answers)
        self.index = 0

    def ask_question(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        response = self.answers[self.index]
        self.index += 1
        return response

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return True

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        pass


scenarios(feature_path(__file__, "general", "interactive_flow_cli.feature"))
scenarios(feature_path(__file__, "general", "interactive_flow_webui.feature"))
scenarios(
    feature_path(__file__, "general", "interactive_requirements_flow_cli.feature")
)
scenarios(
    feature_path(__file__, "general", "interactive_requirements_flow_webui.feature")
)


@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@given("the WebUI is initialized")
def webui_initialized(webui_context):
    return webui_context


@when("I run the interactive requirements flow")
def run_flow(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())
    answers = ["My Project", "python", "feature1,feature2"]
    bridge = DummyBridge(answers)
    output = os.path.join(tmp_project_dir, "interactive_requirements.json")
    collector = RequirementsCollector(bridge, output_file=output)
    collector.gather()


@when("I run the interactive requirements flow in the WebUI")
def run_flow_webui(tmp_project_dir, webui_context):
    webui_context["st"].sidebar.radio.return_value = "Onboarding"
    webui_context["st"].text_input.side_effect = [
        "My Project",
        "python",
        "feature1,feature2",
    ]
    webui_context["st"].checkbox.return_value = True
    output = os.path.join(tmp_project_dir, "interactive_requirements.json")
    collector = RequirementsCollector(webui_context["ui"], output_file=output)
    collector.gather()


@then('an interactive requirements file "interactive_requirements.json" should exist')
def check_interactive_file(tmp_project_dir):
    path = os.path.join(tmp_project_dir, "interactive_requirements.json")
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("name") == "My Project"
