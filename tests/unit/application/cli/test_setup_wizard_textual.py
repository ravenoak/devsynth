"""Ensure Textual bridges stay in sync with CLI behaviour."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from collections.abc import Iterable, Mapping

import pytest

from devsynth.application.cli.config import CLIConfig
from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.application.requirements.wizard import requirements_wizard
from devsynth.domain.models.requirement import RequirementPriority, RequirementType
from devsynth.interface.textual_ui import TextualUXBridge
from devsynth.interface.ux_bridge import UXBridge

pytestmark = [pytest.mark.fast]


class QueueBridge(UXBridge):
    """Bridge that returns queued answers and confirmations."""

    def __init__(self, answers: Iterable[str], confirms: Iterable[bool]) -> None:
        self._answers = list(answers)
        self._confirms = list(confirms)
        self.messages: list[str] = []

    def ask_question(self, *_args, **_kwargs) -> str:
        return self._answers.pop(0)

    def confirm_choice(self, *_args, **_kwargs) -> bool:
        return self._confirms.pop(0)

    def display_result(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None:
        _ = highlight, message_type
        self.messages.append(message)


class ForcedTextualBridge(TextualUXBridge):
    """Textual bridge that advertises pane and shortcut capabilities."""

    @property
    def capabilities(self) -> Mapping[str, bool]:  # pragma: no cover - simple accessor
        base = dict(super().capabilities)
        base["supports_layout_panels"] = True
        base["supports_keyboard_shortcuts"] = True
        return base


def _payload_from_config(config) -> dict[str, object]:
    return {
        "root": Path(config.config.project_root),
        "language": config.config.language,
        "structure": config.config.structure,
        "constraints": config.config.constraints,
        "goals": config.config.goals,
        "memory": config.config.memory_store_type,
        "offline": config.config.offline_mode,
        "features": dict(config.config.features or {}),
    }


def test_textual_and_cli_payloads_match(tmp_path, monkeypatch) -> None:
    """Textual bridges should mirror CLI wizard selections."""

    project_dir = tmp_path / "project"
    project_dir.mkdir(exist_ok=True)

    answers = [
        str(project_dir),
        "python",
        "monorepo",
        "",
        "Deliver robust tooling",
        "file",
    ]
    confirms = [
        False,
        True,
        True,
        False,
        True,
        True,
        False,
        False,
        True,
    ]

    monkeypatch.chdir(tmp_path)
    cli_bridge = QueueBridge(answers, confirms)
    cli_config = SetupWizard(cli_bridge).run()

    config_dir = project_dir / ".devsynth"
    if config_dir.exists():
        shutil.rmtree(config_dir)

    textual_answers = list(answers)
    textual_confirms = list(confirms)
    monkeypatch.chdir(tmp_path)
    textual_bridge = ForcedTextualBridge(
        question_responses=textual_answers,
        confirm_responses=textual_confirms,
    )
    textual_config = SetupWizard(textual_bridge).run()

    assert _payload_from_config(cli_config) == _payload_from_config(textual_config)


def test_requirements_wizard_supports_shortcut_navigation(
    tmp_path, monkeypatch
) -> None:
    """Arrow-key style responses should navigate backwards when supported."""

    workdir = tmp_path / "requirements"
    workdir.mkdir()
    monkeypatch.chdir(workdir)

    answers = [
        "Initial Title",
        "<left>",
        "Final Title",
        "High level description",
        RequirementType.FUNCTIONAL.value,
        RequirementPriority.HIGH.value,
        "Latency < 50ms, GDPR compliant",
    ]
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(workdir))
    bridge = ForcedTextualBridge(question_responses=answers, confirm_responses=[])
    output_file = workdir / "req.json"

    requirements_wizard(
        bridge,
        output_file=str(output_file),
        config=CLIConfig(non_interactive=False),
    )

    data = json.loads(output_file.read_text())
    assert data["title"] == "Final Title"
    assert data["description"] == "High level description"
    assert data["type"] == RequirementType.FUNCTIONAL.value
    assert data["priority"] == RequirementPriority.HIGH.value
    assert data["constraints"] == ["Latency < 50ms", "GDPR compliant"]
