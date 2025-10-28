"""Tests for the Dear PyGUI user interface."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import devsynth.interface.dpg_ui as dpg_ui
from devsynth.domain.models.requirement import RequirementPriority, RequirementType


@pytest.mark.fast
def test_all_buttons_trigger_callbacks_and_progress(monkeypatch):
    """Every button invokes its command and updates progress."""

    fake_dpg = MagicMock()
    fake_dpg.window.return_value.__enter__.return_value = None
    fake_dpg.is_dearpygui_running.side_effect = [False]
    monkeypatch.setattr(dpg_ui, "dpg", fake_dpg)

    funcs: dict[str, MagicMock] = {}

    def _register(name: str, *, with_param: bool = False) -> MagicMock:
        mock = MagicMock()
        mock.__name__ = name
        if with_param:
            mock.side_effect = lambda *_args, bridge: None
        else:
            mock.side_effect = lambda *, bridge: None
        funcs[name] = mock
        return mock

    cli_cmd_names = [
        "init_cmd",
        "gather_cmd",
        "inspect_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "enable_feature_cmd",
        "refactor_cmd",
        "webapp_cmd",
        "serve_cmd",
        "dbschema_cmd",
        "doctor_cmd",
        "check_cmd",
        "webui_cmd",
        "inspect_code_cmd",
        "edrr_cycle_cmd",
        "ingest_cmd",
    ]
    cli_funcs = {
        name: _register(name, with_param=(name == "enable_feature_cmd"))
        for name in cli_cmd_names
    }

    other_cmds = {
        "apispec_cmd": _register("apispec_cmd"),
        "align_cmd": _register("align_cmd"),
        "alignment_metrics_cmd": _register("alignment_metrics_cmd"),
        "inspect_config_cmd": _register("inspect_config_cmd"),
        "validate_manifest_cmd": _register("validate_manifest_cmd"),
        "validate_metadata_cmd": _register("validate_metadata_cmd"),
        "test_metrics_cmd": _register("test_metrics_cmd"),
        "generate_docs_cmd": _register("generate_docs_cmd"),
    }

    fake_cli = SimpleNamespace(**cli_funcs)
    fake_apispec = SimpleNamespace(apispec_cmd=other_cmds["apispec_cmd"])
    fake_commands = SimpleNamespace(
        align_cmd=other_cmds["align_cmd"],
        alignment_metrics_cmd=other_cmds["alignment_metrics_cmd"],
        inspect_config_cmd=other_cmds["inspect_config_cmd"],
        validate_manifest_cmd=other_cmds["validate_manifest_cmd"],
        validate_metadata_cmd=other_cmds["validate_metadata_cmd"],
        test_metrics_cmd=other_cmds["test_metrics_cmd"],
        generate_docs_cmd=other_cmds["generate_docs_cmd"],
    )

    monkeypatch.setitem(sys.modules, "devsynth.application.cli", fake_cli)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.apispec", fake_apispec)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.commands", fake_commands)

    class FakeProgress:
        def __init__(self) -> None:
            self.update = MagicMock()
            self.complete = MagicMock()
            self._current = 0
            self._total = 100

    class DummyBridge:
        instance: DummyBridge | None = None

        def __init__(self) -> None:
            DummyBridge.instance = self
            self.progresses: list[FakeProgress] = []

        def run_cli_command(self, cmd, *, progress_hook=None):
            progress = FakeProgress()
            self.progresses.append(progress)
            if progress_hook:
                progress_hook(progress)
                progress_hook(progress)
            cmd(bridge=self)
            progress.complete()

        def ask_question(self, _prompt: str) -> str:
            return "feat"

    monkeypatch.setattr(dpg_ui, "DearPyGUIBridge", DummyBridge)

    dpg_ui.run()

    callbacks = {
        call.kwargs["label"]: call.kwargs["callback"]
        for call in fake_dpg.add_button.call_args_list
    }

    bridge = DummyBridge.instance
    assert bridge is not None

    label_to_name = [
        ("Init", "init_cmd"),
        ("Gather", "gather_cmd"),
        ("Inspect", "inspect_cmd"),
        ("Spec", "spec_cmd"),
        ("Test", "test_cmd"),
        ("Code", "code_cmd"),
        ("Run Pipeline", "run_pipeline_cmd"),
        ("Config", "config_cmd"),
        ("Enable Feature", "enable_feature_cmd"),
        ("Inspect Code", "inspect_code_cmd"),
        ("Refactor", "refactor_cmd"),
        ("Webapp", "webapp_cmd"),
        ("Serve", "serve_cmd"),
        ("DbSchema", "dbschema_cmd"),
        ("Doctor", "doctor_cmd"),
        ("Check", "check_cmd"),
        ("EDRR Cycle", "edrr_cycle_cmd"),
        ("Align", "align_cmd"),
        ("Alignment Metrics", "alignment_metrics_cmd"),
        ("Inspect Config", "inspect_config_cmd"),
        ("Validate Manifest", "validate_manifest_cmd"),
        ("Validate Metadata", "validate_metadata_cmd"),
        ("Test Metrics", "test_metrics_cmd"),
        ("Generate Docs", "generate_docs_cmd"),
        ("Ingest", "ingest_cmd"),
        ("API Spec", "apispec_cmd"),
        ("WebUI", "webui_cmd"),
    ]

    for label, name in label_to_name:
        cb = callbacks[label]
        cb()
        funcs[name].assert_called_once()
        progress = bridge.progresses[-1]
        assert progress.update.call_count >= 2
        progress.complete.assert_called_once()

    assert "Wizard" in callbacks
    assert funcs["enable_feature_cmd"].call_args[0] == ("feat",)


@pytest.mark.fast
def test_requirements_wizard_dialog(tmp_path, monkeypatch):
    """Wizard dialog saves requirements and shows progress."""

    answers = iter(
        [
            "My title",
            "My description",
            RequirementType.FUNCTIONAL.value,
            RequirementPriority.HIGH.value,
            "c1, c2",
        ]
    )

    update_calls: list[tuple[int, str | None]] = []

    class FakeProgress:
        def update(self, advance: int = 0, description: str | None = None) -> None:
            update_calls.append((advance, description))

        def complete(self) -> None:  # pragma: no cover - simple
            pass

    class FakeBridge:
        def __init__(self) -> None:
            self.messages: list[str] = []

        def ask_question(self, *_args, **_kwargs) -> str:
            return next(answers)

        def create_progress(self, *_args, **_kwargs) -> FakeProgress:
            return FakeProgress()

        def display_result(self, message: str, **_kwargs) -> None:
            self.messages.append(message)

    monkeypatch.chdir(tmp_path)
    bridge = FakeBridge()
    dpg_ui._requirements_wizard_dialog(bridge)

    with open(tmp_path / "requirements_wizard.json", encoding="utf-8") as fh:
        data = json.load(fh)

    assert data["title"] == "My title"
    assert data["priority"] == RequirementPriority.HIGH.value
    assert "[green]Requirements saved" in bridge.messages[-1]
    descriptions = [d for _a, d in update_calls if d]
    assert descriptions[0].startswith("Step 1/5")


@pytest.mark.fast
def test_requirements_wizard_dialog_error(monkeypatch, tmp_path):
    """Errors in wizard are reported and progress closed."""

    answers = iter(["t", "d", "functional", "medium", "c"])

    class FakeProgress:
        def __init__(self) -> None:
            self.completed = False

        def update(self, advance: int = 0, description: str | None = None) -> None:
            pass

        def complete(self) -> None:
            self.completed = True

    class FakeBridge:
        def __init__(self) -> None:
            self.messages: list[str] = []
            self.progress: FakeProgress | None = None

        def ask_question(self, *_args, **_kwargs) -> str:
            return next(answers)

        def create_progress(self, *_args, **_kwargs) -> FakeProgress:
            self.progress = FakeProgress()
            return self.progress

        def display_result(self, message: str, **_kwargs) -> None:
            self.messages.append(message)

    def boom(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr("builtins.open", boom)
    bridge = FakeBridge()
    dpg_ui._requirements_wizard_dialog(bridge)

    assert any("ERROR in requirements wizard" in m for m in bridge.messages)
    assert bridge.progress is not None and bridge.progress.completed
