from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Sequence
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

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
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        return self.answers.pop(0)

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return self.confirms.pop(0)

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        pass


scenarios(feature_path(__file__, "general", "setup_wizard.feature"))


@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@when("I run the setup wizard")
def run_setup_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(os.sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(os.sys.modules, "uvicorn", MagicMock())
    from devsynth.application.cli.setup_wizard import SetupWizard

    wizard = SetupWizard(DummyBridge([], []))
    wizard.run(
        root=str(tmp_project_dir),
        structure="single_package",
        language="python",
        constraints="",
        goals="demo goals",
        memory_backend="kuzu",
        offline_mode=True,
        features={"wsde_collaboration": True},
        auto_confirm=True,
    )


@when("I cancel the setup wizard")
def cancel_setup_wizard(tmp_project_dir, monkeypatch):
    monkeypatch.setitem(os.sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(os.sys.modules, "uvicorn", MagicMock())
    from devsynth.application.cli.setup_wizard import SetupWizard

    wizard = SetupWizard(DummyBridge([], [False]))
    wizard.run(
        root=str(tmp_project_dir),
        structure="single_package",
        language="python",
        constraints="",
        goals="",
        memory_backend="memory",
        offline_mode=False,
        features={
            "wsde_collaboration": False,
            "dialectical_reasoning": False,
            "code_generation": False,
            "test_generation": False,
            "documentation_generation": False,
            "experimental_features": False,
        },
        auto_confirm=False,
    )


@then("a project configuration file should include the selected options")
def check_config(tmp_project_dir):
    from devsynth.config.unified_loader import UnifiedConfigLoader

    cfg = UnifiedConfigLoader.load(tmp_project_dir).config
    assert cfg.memory_store_type == "kuzu"
    assert cfg.offline_mode is True
    assert cfg.features["wsde_collaboration"] is True


@then("no project configuration file should exist")
def no_config(tmp_project_dir):
    cfg_file = Path(tmp_project_dir) / ".devsynth" / "project.yaml"
    assert not cfg_file.exists()
