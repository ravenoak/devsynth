from __future__ import annotations

import logging
from pathlib import Path

import pytest
import yaml
from pytest_bdd import given, scenarios, then, when

from devsynth.application.requirements.wizard import requirements_wizard
from devsynth.interface.ux_bridge import UXBridge
from devsynth.utils.logging import configure_logging
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]


class DummyBridge(UXBridge):
    def __init__(self, answers):
        self.answers = list(answers)

    def ask_question(
        self, message: str, *, choices=None, default=None, show_default=True
    ):
        return self.answers.pop(0)

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return True

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        pass


scenarios(feature_path(__file__, "general", "requirements_wizard_logging.feature"))


@given("logging is configured for the requirements wizard")
def logging_configured(tmp_path, monkeypatch):
    import os

    os.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    configure_logging("INFO")


@when('I run the requirements wizard with priority "high"')
def run_wizard(caplog):
    answers = ["Title", "Desc", "functional", "high", ""]
    bridge = DummyBridge(answers)
    with caplog.at_level(logging.INFO):
        requirements_wizard(bridge, output_file="req.json")


@then('the log should include the priority "high"')
def log_contains_priority(caplog):
    assert any(
        getattr(rec, "step", None) == "priority"
        and getattr(rec, "value", None) == "high"
        for rec in caplog.records
    )


@then('the configuration file should record priority "high"')
def config_has_priority(tmp_path):
    cfg = yaml.safe_load((tmp_path / ".devsynth" / "project.yaml").read_text())
    assert cfg["priority"] == "high"
