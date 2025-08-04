"""Tests for the Dear PyGUI user interface."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import sys
import threading
import time as real_time

import devsynth.interface.dpg_ui as dpg_ui


def test_all_buttons_trigger_callbacks_and_progress(monkeypatch):
    """Every button invokes its command and updates progress."""

    fake_dpg = MagicMock()
    fake_dpg.window.return_value.__enter__.return_value = None
    fake_dpg.is_dearpygui_running.side_effect = [False]
    monkeypatch.setattr(dpg_ui, "dpg", fake_dpg)

    threads: list[threading.Thread] = []
    real_thread = threading.Thread

    class ThreadRecorder:
        def __init__(self, target, daemon=False):
            self._t = real_thread(target=target, daemon=daemon)
            threads.append(self._t)

        def start(self) -> None:  # pragma: no cover - simple proxy
            self._t.start()

    monkeypatch.setattr(dpg_ui.threading, "Thread", ThreadRecorder)
    monkeypatch.setattr(dpg_ui.time, "sleep", lambda _x: None)

    events: dict[str, threading.Event] = {}
    funcs: dict[str, MagicMock] = {}

    def _register(name: str, *, with_param: bool = False) -> MagicMock:
        event = threading.Event()
        events[name] = event
        mock = MagicMock()
        mock.__name__ = name

        if with_param:
            mock.side_effect = lambda *_args, bridge, _event=event: _event.wait()
        else:
            mock.side_effect = lambda *, bridge, _event=event: _event.wait()

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
    cli_funcs = {name: _register(name, with_param=(name == "enable_feature_cmd")) for name in cli_cmd_names}

    other_cmds = {
        "wizard_cmd": _register("wizard_cmd"),
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
    fake_requirements = SimpleNamespace(wizard_cmd=other_cmds["wizard_cmd"])
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
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.requirements_commands", fake_requirements
    )
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.commands", fake_commands)

    class DummyBridge:
        instance: "DummyBridge" | None = None

        def __init__(self) -> None:
            DummyBridge.instance = self
            self.progresses: list[FakeProgress] = []

        def create_progress(self, _msg: str):
            progress = FakeProgress()
            self.progresses.append(progress)
            return progress

        def ask_question(self, _prompt: str) -> str:
            return "feat"

    class FakeProgress:
        def __init__(self) -> None:
            self.update = MagicMock(side_effect=self._update)
            self.complete = MagicMock()
            self._current = 0
            self._total = 100

        def _update(self, advance: int = 1, description: str | None = None) -> None:
            self._current += advance

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
        ("Wizard", "wizard_cmd"),
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
        pre = len(threads)
        cb = callbacks[label]
        cb()
        progress = bridge.progresses[-1]
        while progress.update.call_count == 0:
            real_time.sleep(0.01)
        events[name].set()
        for t in threads[pre:]:
            t.join()

        funcs[name].assert_called_once()
        assert progress.update.call_count > 0
        progress.complete.assert_called_once()

    assert funcs["enable_feature_cmd"].call_args[0] == ("feat",)

