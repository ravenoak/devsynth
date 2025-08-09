import json
import os

import pytest
import yaml

# Ensures gather_requirements persists priority, goals, and constraints
pytestmark = pytest.mark.usefixtures("stub_optional_deps")

from devsynth.application.cli.requirements_wizard import requirements_wizard
from devsynth.application.requirements.interactions import gather_requirements


def test_gather_updates_config_succeeds(tmp_path, monkeypatch):
    """Test that gather updates config succeeds.

    ReqID: N/A"""
    os.chdir(tmp_path)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    os.makedirs(".devsynth", exist_ok=True)
    with open(".devsynth/project.yaml", "w", encoding="utf-8") as f:
        f.write("{}")
    answers = ["goal1", "constraint1", "high"]

    class Bridge:
        def __init__(self):
            self.i = 0

        def ask_question(self, *a, **k):
            val = answers[self.i]
            self.i += 1
            return val

        def prompt(self, *a, **k):
            return self.ask_question(*a, **k)

        def confirm_choice(self, *a, **k):
            return True

        def confirm(self, *a, **k):
            return True

        def display_result(self, *a, **k):
            pass

    bridge = Bridge()
    output = tmp_path / "requirements_plan.yaml"
    gather_requirements(bridge, output_file=str(output))

    cfg_path = tmp_path / ".devsynth" / "project.yaml"
    data = yaml.safe_load(open(cfg_path, encoding="utf-8"))
    assert data.get("priority") == "high"
    assert data.get("goals") == "goal1"
    assert data.get("constraints") == "constraint1"

    plan = yaml.safe_load(open(output, encoding="utf-8"))
    assert plan["priority"] == "high"
    assert plan["goals"] == ["goal1"]
    assert plan["constraints"] == ["constraint1"]


def test_requirements_wizard_persists_priority_succeeds(tmp_path, monkeypatch):
    """Interactive requirements wizard should persist priority."""
    os.chdir(tmp_path)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    answers = [
        "My Title",
        "A description",
        "functional",
        "high",
        "c1,c2",
    ]

    class Bridge:
        def __init__(self):
            self.i = 0

        def ask_question(self, *a, **k):
            val = answers[self.i]
            self.i += 1
            return val

        def display_result(self, *a, **k):
            pass

    bridge = Bridge()
    output = tmp_path / "requirements_wizard.json"
    requirements_wizard(bridge, output_file=str(output))
    data = json.load(open(output, encoding="utf-8"))
    assert data["priority"] == "high"
    assert data["title"] == "My Title"
    assert data["description"] == "A description"
