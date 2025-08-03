import json
import yaml
from types import ModuleType
from unittest.mock import MagicMock
import pytest
from devsynth.application.cli import requirements_commands as rc
from devsynth.interface.ux_bridge import UXBridge

class DummyBridge(UXBridge):

    def __init__(self, answers):
        self.answers = list(answers)

    def ask_question(self, *_a, **_k):
        return self.answers.pop(0)

    def confirm_choice(self, *_a, **_k):
        return True

    def display_result(self, *_a, **_k):
        pass

@pytest.mark.medium
def test_wizard_cmd_back_navigation_succeeds(tmp_path, monkeypatch):
    """Users should be able to revise answers using 'back'."""
    monkeypatch.setattr(rc, 'NON_INTERACTIVE', False)
    answers = ['Old title', 'back', 'New title', 'Description', 'functional', 'medium', '']
    bridge = DummyBridge(answers)
    output = tmp_path / 'req.json'
    rc.wizard_cmd(output_file=str(output), bridge=bridge)
    data = json.load(open(output))
    assert data['title'] == 'New title'
    assert data['priority'] == 'medium'

@pytest.mark.medium
def test_gather_requirements_cmd_yaml_succeeds(tmp_path, monkeypatch):
    """gather_requirements_cmd should write YAML output."""

    class Bridge(DummyBridge):

        def prompt(self, *a, **k):
            return self.ask_question()

        def confirm(self, *a, **k):
            return True
    answers = ['goal1', 'constraint1', 'high']
    bridge = Bridge(answers)
    output = tmp_path / 'requirements_plan.yaml'
    monkeypatch.chdir(tmp_path)
    rc.gather_requirements_cmd(output_file=str(output), bridge=bridge)
    assert output.exists()
    data = yaml.safe_load(open(output))
    assert data['priority'] == 'high'