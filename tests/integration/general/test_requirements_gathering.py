import json
import logging
import os

import pytest
import yaml
from _pytest.logging import LogCaptureHandler

# ``json`` is used to verify the wizard's output file contents

# Ensures gather_requirements persists priority, goals, and constraints
pytestmark = [
    pytest.mark.usefixtures("stub_optional_deps")
]  # keep resource/fixtures at module scope

from devsynth.application.cli import requirements_commands as rc
from devsynth.application.cli.config import CLIConfig
from devsynth.application.cli.errors import handle_error
from devsynth.application.cli.requirements_wizard import requirements_wizard
from devsynth.application.requirements.interactions import gather_requirements
from devsynth.logging_setup import configure_logging


@pytest.mark.medium
def test_gather_updates_config_succeeds(tmp_path, monkeypatch):
    """Test that gather updates config succeeds.

    ReqID: FR-81"""
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


@pytest.mark.medium
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
    requirements_wizard(bridge, output_file=str(output), config=CLIConfig())
    data = json.load(open(output, encoding="utf-8"))
    assert data["priority"] == "high"
    assert data["title"] == "My Title"
    assert data["description"] == "A description"

    cfg_path = tmp_path / ".devsynth" / "project.yaml"
    cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))
    assert cfg.get("priority") == "high"
    assert cfg.get("constraints") == "c1,c2"


@pytest.mark.medium
def test_requirements_wizard_backtracks_priority_succeeds(tmp_path, monkeypatch):
    """Priority persists when navigating back and changing choices."""
    os.chdir(tmp_path)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    answers = [
        "Title",  # title
        "Desc",  # description
        "functional",  # type
        "low",  # initial priority
        "back",  # go back from constraints to priority
        "high",  # updated priority
        "c1",  # constraints
    ]

    class Bridge:
        def __init__(self):
            self.i = 0

        def ask_question(self, *a, **k):
            val = answers[self.i]
            self.i += 1
            return val

        def display_result(self, *a, **k):  # pragma: no cover - no output
            pass

    bridge = Bridge()
    output = tmp_path / "requirements_wizard_back.json"
    requirements_wizard(bridge, output_file=str(output), config=CLIConfig())
    data = json.load(open(output, encoding="utf-8"))
    assert data["priority"] == "high"

    cfg_path = tmp_path / ".devsynth" / "project.yaml"
    cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))
    assert cfg.get("priority") == "high"


@pytest.mark.medium
def test_gather_cmd_logging_exc_info_succeeds(tmp_path, monkeypatch):
    """gather_requirements_cmd logs exceptions without crashing."""
    os.chdir(tmp_path)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    configure_logging(create_dir=False)
    handler = LogCaptureHandler()
    logging.getLogger().addHandler(handler)

    def boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr("devsynth.core.workflows.gather_requirements", boom)

    class Bridge:
        def display_result(self, *_a, **_k):  # pragma: no cover - no output
            pass

        def handle_error(self, *_a, **_k):  # pragma: no cover - no output
            pass

    bridge = Bridge()
    try:
        rc.gather_requirements_cmd(bridge=bridge)
    except RuntimeError as err:
        handle_error(bridge, err)

    logging.getLogger().removeHandler(handler)
    record = next(rec for rec in handler.records if rec.exc_info)
    assert record.exc_info[0] is RuntimeError
