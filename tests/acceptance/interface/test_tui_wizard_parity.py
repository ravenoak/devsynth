"""Acceptance tests that ensure CLI and Textual wizards stay in sync."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from collections.abc import Iterable, Sequence

import pytest

from devsynth.application.cli.config import CLIConfig
from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.application.requirements.wizard import requirements_wizard
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.textual_ui import TextualUXBridge

pytestmark = [pytest.mark.fast]


class AutomatedCLIUXBridge(CLIUXBridge):
    """CLI bridge that replays scripted answers for deterministic tests."""

    def __init__(
        self,
        answers: Sequence[str],
        confirms: Sequence[bool],
        *,
        colorblind_mode: bool | None = None,
    ) -> None:
        super().__init__(colorblind_mode=colorblind_mode)
        self._answers = list(answers)
        self._confirms = list(confirms)

    def ask_question(
        self,
        message: str,
        *,
        choices: Iterable[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        _ = message, choices, show_default
        if self._answers:
            return self._answers.pop(0)
        return default or ""

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        _ = message
        if self._confirms:
            return self._confirms.pop(0)
        return default


def _snapshot_directory(root: Path) -> dict[str, str]:
    """Return a mapping of relative paths to file contents for comparison."""

    snapshot: dict[str, str] = {}
    for file in sorted(root.rglob("*")):
        if file.is_file():
            snapshot[file.relative_to(root).as_posix()] = file.read_text()
    return snapshot


def test_setup_wizard_cli_and_textual_outputs_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Setup wizard should produce identical artifacts via CLI and Textual bridges."""

    project_dir = tmp_path / "demo"
    project_dir.mkdir()

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
    cli_bridge = AutomatedCLIUXBridge(answers, confirms, colorblind_mode=False)
    cli_config = SetupWizard(cli_bridge).run()
    cli_snapshot = _snapshot_directory(project_dir)

    shutil.rmtree(project_dir)
    project_dir.mkdir()

    textual_bridge = TextualUXBridge(
        question_responses=list(answers),
        confirm_responses=list(confirms),
        colorblind_mode=False,
    )
    monkeypatch.setenv("DEVSYNTH_TUI_AUTOMATED", "1")
    textual_config = SetupWizard(textual_bridge).run()
    textual_snapshot = _snapshot_directory(project_dir)

    assert cli_snapshot == textual_snapshot

    def _payload(config) -> dict[str, object]:
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

    assert _payload(cli_config) == _payload(textual_config)


def test_requirements_wizard_cli_and_textual_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Requirements wizard should persist the same data through both bridges."""

    monkeypatch.chdir(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir(exist_ok=True)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_root))

    cli_output = Path("cli_requirements.json")
    tui_output = Path("tui_requirements.json")

    answers = [
        "Initial Title",
        "Refined Title",
        "Functional",
        "High",
        "Latency < 50ms, GDPR compliant",
    ]

    cli_bridge = AutomatedCLIUXBridge(answers, [], colorblind_mode=False)
    requirements_wizard(
        cli_bridge,
        output_file=str(cli_output),
        config=CLIConfig(non_interactive=False),
    )
    cli_data = json.loads((project_root / cli_output).read_text())
    cli_cfg_path = project_root / ".devsynth" / "project.yaml"
    cli_project_cfg = cli_cfg_path.read_text() if cli_cfg_path.exists() else ""

    shutil.rmtree(project_root / ".devsynth")

    textual_bridge = TextualUXBridge(
        question_responses=list(answers),
        confirm_responses=[],
        colorblind_mode=False,
    )
    monkeypatch.setenv("DEVSYNTH_TUI_AUTOMATED", "1")
    requirements_wizard(
        textual_bridge,
        output_file=str(tui_output),
        config=CLIConfig(non_interactive=False),
    )

    tui_data = json.loads((project_root / tui_output).read_text())
    assert cli_data == tui_data

    tui_cfg_path = project_root / ".devsynth" / "project.yaml"
    tui_project_cfg = tui_cfg_path.read_text() if tui_cfg_path.exists() else ""
    assert cli_project_cfg == tui_project_cfg
