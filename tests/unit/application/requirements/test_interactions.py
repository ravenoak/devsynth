"""Unit tests for interactive requirements collection helpers."""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Iterable

import pytest
import yaml

from devsynth.application.requirements import interactions
from devsynth.application.requirements.interactions import (
    RequirementsCollector,
    gather_requirements,
)
from devsynth.interface.ux_bridge import UXBridge

pytestmark = pytest.mark.fast


class CollectorBridge(UXBridge):
    """Bridge stub for :class:`RequirementsCollector`."""

    def __init__(self, answers: Iterable[str], *, confirm: bool = True) -> None:
        self._answers = iter(answers)
        self._confirm = confirm
        self.messages: list[str] = []

    def ask_question(
        self,
        message: str,
        *,
        choices=None,
        default=None,
        show_default: bool = True,
    ) -> str:
        return next(self._answers)

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return self._confirm

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        self.messages.append(message)


def test_requirements_collector_writes_json(tmp_path: Path) -> None:
    """Collected answers are serialized and reported through the bridge."""

    bridge = CollectorBridge(["Project", "python", "api;docs"], confirm=True)
    output = tmp_path / "requirements.json"

    RequirementsCollector(bridge, output_file=str(output)).gather()

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["name"] == "Project"
    assert data["language"] == "python"
    assert data["features"] == ["api", "docs"]
    assert bridge.messages[-1] == "Requirements saved"


def test_requirements_collector_cancelled(tmp_path: Path) -> None:
    """Cancelling the collector avoids writing an output file."""

    bridge = CollectorBridge(["Project", "python", "api,docs"], confirm=False)
    output = tmp_path / "requirements.json"

    RequirementsCollector(bridge, output_file=str(output)).gather()

    assert not output.exists()
    assert bridge.messages[-1] == "Cancelled"


class GatherBridge(UXBridge):
    """Bridge stub that records prompts for ``gather_requirements``."""

    def __init__(self, answers: Iterable[str]) -> None:
        self._answers = iter(answers)
        self.messages: list[str] = []

    def ask_question(
        self,
        message: str,
        *,
        choices=None,
        default=None,
        show_default: bool = True,
    ) -> str:
        return next(self._answers)

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return True

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        self.messages.append(message)


def test_gather_requirements_supports_backtracking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gatherer handles "back" navigation and persists to YAML plus config."""

    answers = ["back", "goal1,goal2", "latency<100ms", "high"]
    bridge = GatherBridge(answers)
    output = tmp_path / "requirements.yaml"

    class DummyConfig:
        def __init__(self) -> None:
            self.goals: list[str] = []
            self.constraints: list[str] = []
            self.priority: str = "medium"

    saved = {}

    monkeypatch.setattr(interactions, "get_project_config", lambda _path: DummyConfig())

    def fake_save(cfg: DummyConfig, *, use_pyproject: bool) -> None:
        saved["cfg"] = cfg

    monkeypatch.setattr(interactions, "save_config", fake_save)

    gather_requirements(bridge, output_file=str(output))

    loaded = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert loaded == {
        "goals": ["goal1", "goal2"],
        "constraints": ["latency<100ms"],
        "priority": "high",
    }

    assert isinstance(saved["cfg"], DummyConfig)
    assert saved["cfg"].goals == "goal1,goal2"
    assert saved["cfg"].constraints == "latency<100ms"
    assert saved["cfg"].priority == "high"

    assert bridge.messages[0] == "[yellow]Already at first step.[/yellow]"
    assert bridge.messages[-1] == f"[green]Requirements saved to {output}[/green]"
