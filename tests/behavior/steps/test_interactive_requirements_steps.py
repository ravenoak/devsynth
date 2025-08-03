import os
import json
import sys
from unittest.mock import MagicMock

import pytest
from pytest_bdd import scenarios, given, when, then


scenarios("../features/general/interactive_requirements.feature")


@pytest.mark.medium
@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@pytest.mark.medium
@when("I run the interactive requirements wizard")
def run_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())
    from devsynth.application.cli.requirements_commands import wizard_cmd

    output = os.path.join(tmp_project_dir, "requirements_wizard.json")
    monkeypatch.setenv("DEVSYNTH_REQ_TITLE", "Sample title")
    monkeypatch.setenv("DEVSYNTH_REQ_DESCRIPTION", "Sample description")
    monkeypatch.setenv("DEVSYNTH_REQ_TYPE", "functional")
    monkeypatch.setenv("DEVSYNTH_REQ_PRIORITY", "medium")
    monkeypatch.setenv("DEVSYNTH_REQ_CONSTRAINTS", "")
    monkeypatch.setenv("DEVSYNTH_NONINTERACTIVE", "1")
    wizard_cmd(output_file=output)


@pytest.mark.medium
@then('a structured requirements file "requirements_wizard.json" should exist')
def check_file(tmp_project_dir):
    path = os.path.join(tmp_project_dir, "requirements_wizard.json")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("title") == "Sample title"
