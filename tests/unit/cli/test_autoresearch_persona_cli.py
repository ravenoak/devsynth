"""Tests for the autoresearch CLI command."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


def _load_command():
    """Import the CLI command with a lightweight rich stub."""

    if "rich.console" not in sys.modules:
        rich_module = types.ModuleType("rich")
        console_module = types.ModuleType("rich.console")
        table_module = types.ModuleType("rich.table")
        markdown_module = types.ModuleType("rich.markdown")
        panel_module = types.ModuleType("rich.panel")
        progress_module = types.ModuleType("rich.progress")
        prompt_module = types.ModuleType("rich.prompt")
        style_module = types.ModuleType("rich.style")
        text_module = types.ModuleType("rich.text")
        theme_module = types.ModuleType("rich.theme")

        class _Console:  # pragma: no cover - trivial stub
            def __init__(self, *_, **__):
                pass

            def print(self, *_, **__):
                pass

        console_module.Console = _Console
        table_module.Table = object
        markdown_module.Markdown = object
        panel_module.Panel = object
        progress_module.Progress = object
        progress_module.BarColumn = object
        progress_module.MofNCompleteColumn = object
        progress_module.SpinnerColumn = object
        progress_module.TextColumn = object
        progress_module.TimeElapsedColumn = object
        progress_module.TimeRemainingColumn = object
        prompt_module.Confirm = object
        prompt_module.Prompt = object
        style_module.Style = object
        text_module.Text = object
        theme_module.Theme = object
        rich_module.console = console_module
        sys.modules["rich"] = rich_module
        sys.modules["rich.console"] = console_module
        sys.modules["rich.table"] = table_module
        sys.modules["rich.markdown"] = markdown_module
        sys.modules["rich.panel"] = panel_module
        sys.modules["rich.progress"] = progress_module
        sys.modules["rich.prompt"] = prompt_module
        sys.modules["rich.style"] = style_module
        sys.modules["rich.text"] = text_module
        sys.modules["rich.theme"] = theme_module

    if "toml" not in sys.modules:
        toml_module = types.ModuleType("toml")

        def _loads(_: str) -> dict[str, object]:  # pragma: no cover - simple stub
            return {}

        toml_module.loads = _loads
        toml_module.load = lambda *_args, **_kwargs: {}
        sys.modules["toml"] = toml_module

    if "yaml" not in sys.modules:
        yaml_module = types.ModuleType("yaml")

        def _safe_load(_: object) -> dict[str, object]:  # pragma: no cover - simple stub
            return {}

        yaml_module.safe_load = _safe_load
        sys.modules["yaml"] = yaml_module

    if "devsynth.config" not in sys.modules:
        config_module = types.ModuleType("devsynth.config")

        class _DummyConfig:
            pass

        def _get_project_config(*_args, **_kwargs):  # pragma: no cover - stub
            return _DummyConfig()

        def _save_config(*_args, **_kwargs) -> None:  # pragma: no cover - stub
            return None

        config_module.get_project_config = _get_project_config
        config_module.save_config = _save_config
        sys.modules["devsynth.config"] = config_module

    if "devsynth" not in sys.modules:
        sys.modules["devsynth"] = types.ModuleType("devsynth")

    if "devsynth.core" not in sys.modules:
        sys.modules["devsynth.core"] = types.ModuleType("devsynth.core")

    if "devsynth.core.mvu" not in sys.modules:
        sys.modules["devsynth.core.mvu"] = types.ModuleType("devsynth.core.mvu")

    if "devsynth.core.mvu.models" not in sys.modules:
        mvu_module = types.ModuleType("devsynth.core.mvu.models")

        class _StubMVUU:
            def __init__(self, **kwargs):
                self._data = kwargs

            def as_dict(self) -> dict[str, object]:  # pragma: no cover - simple stub
                return dict(self._data)

        mvu_module.MVUU = _StubMVUU
        sys.modules["devsynth.core.mvu.models"] = mvu_module
        sys.modules["devsynth.core"].mvu = types.SimpleNamespace(models=mvu_module)

    module_name = "__autoresearch_cli_cmd__"
    if module_name in sys.modules and hasattr(sys.modules[module_name], "autoresearch_cmd"):
        return sys.modules[module_name].autoresearch_cmd

    sys.modules.pop(module_name, None)
    base_path = Path(__file__).resolve().parents[3]
    module_path = base_path / "src" / "devsynth" / "application" / "cli" / "commands" / "autoresearch_cmd.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.autoresearch_cmd


@pytest.mark.fast
def test_autoresearch_cli_emits_trace(capfd, monkeypatch):
    """The command should emit MVUU trace metadata when enabled."""

    autoresearch_cmd = _load_command()
    module = sys.modules["__autoresearch_cli_cmd__"]

    class _StubCoordinator:
        def __init__(self):
            self.research_persona_preferences: list[str] = []
            self.research_persona_telemetry: list[dict[str, object]] = []

        def configure_personas(self, enabled: bool, personas: list[str]) -> list[str]:
            self.research_persona_preferences = personas if enabled else []
            self.research_persona_telemetry.append({"event": "configured"})
            return self.research_persona_preferences

        def create_team(self, _team_id: str):
            class _Team:
                name = "stub"

                def enable_research_personas(self, *_args, **_kwargs):
                    return []

            return _Team()

        def _record_persona_event(self, event: str, payload: dict[str, object]) -> None:
            self.research_persona_telemetry.append({"event": event, "payload": payload})

    monkeypatch.setattr(module, "WSDETeamCoordinator", _StubCoordinator)

    exit_code = autoresearch_cmd(
        ["--enable-personas", "--persona", "research_lead", "--trace-id", "TRACE-123"]
    )
    assert exit_code == 0
    captured = capfd.readouterr()
    payload = json.loads(captured.out)
    assert payload["personas"] == ["research_lead"]
    assert payload["mvuu"]["TraceID"] == "TRACE-123"
    assert payload["mvuu"]["mvuu"] is True


@pytest.mark.fast
def test_autoresearch_cli_handles_no_trace(capfd, monkeypatch):
    """The --no-trace flag suppresses MVUU emission."""

    autoresearch_cmd = _load_command()
    module = sys.modules["__autoresearch_cli_cmd__"]

    class _StubCoordinator:
        def __init__(self):
            self.research_persona_preferences: list[str] = []
            self.research_persona_telemetry: list[dict[str, object]] = []

        def configure_personas(self, enabled: bool, personas: list[str]) -> list[str]:
            self.research_persona_preferences = personas if enabled else []
            return self.research_persona_preferences

        def create_team(self, _team_id: str):
            class _Team:
                name = "stub"

                def enable_research_personas(self, *_args, **_kwargs):
                    return []

            return _Team()

        def _record_persona_event(self, event: str, payload: dict[str, object]) -> None:
            self.research_persona_telemetry.append({"event": event, "payload": payload})

    monkeypatch.setattr(module, "WSDETeamCoordinator", _StubCoordinator)

    exit_code = autoresearch_cmd(["--no-trace"])
    assert exit_code == 0
    captured = capfd.readouterr()
    payload = json.loads(captured.out)
    assert payload["personas"] == []
    assert "mvuu" not in payload
