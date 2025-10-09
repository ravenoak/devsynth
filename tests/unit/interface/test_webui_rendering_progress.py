"""Progress summary rendering for the gather wizard."""

from __future__ import annotations

import importlib.util
import sys
import time
import types
from typing import Any
from unittest.mock import MagicMock

import pytest

if importlib.util.find_spec("argon2") is None:
    argon2_stub = types.ModuleType("argon2")

    class PasswordHasher:  # pragma: no cover - minimal stub
        def __init__(self, *args: object, **kwargs: object) -> None:
            return None

        def hash(self, value: str) -> str:
            return value

        def verify(self, hashed: str, plain: str) -> bool:
            return hashed == plain

    argon2_stub.PasswordHasher = PasswordHasher  # type: ignore[attr-defined]
    exceptions_stub = types.ModuleType("argon2.exceptions")

    class VerifyMismatchError(Exception):
        pass

    exceptions_stub.VerifyMismatchError = VerifyMismatchError
    argon2_stub.exceptions = exceptions_stub  # type: ignore[attr-defined]
    sys.modules["argon2"] = argon2_stub
    sys.modules["argon2.exceptions"] = exceptions_stub

if importlib.util.find_spec("jsonschema") is None:
    jsonschema_stub = types.ModuleType("jsonschema")

    class ValidationError(Exception):
        pass

    def validate(instance: object, schema: object) -> None:  # pragma: no cover
        return None

    jsonschema_stub.ValidationError = ValidationError
    jsonschema_stub.validate = validate  # type: ignore[attr-defined]
    sys.modules["jsonschema"] = jsonschema_stub

if importlib.util.find_spec("toml") is None:
    toml_stub = types.ModuleType("toml")

    def load(
        file: object, *args: object, **kwargs: object
    ) -> dict[str, object]:  # pragma: no cover
        return {}

    def loads(
        text: str, *args: object, **kwargs: object
    ) -> dict[str, object]:  # pragma: no cover
        return {}

    def dump(
        data: object, file: object, *args: object, **kwargs: object
    ) -> None:  # pragma: no cover
        return None

    def dumps(data: object, *args: object, **kwargs: object) -> str:  # pragma: no cover
        return ""

    toml_stub.load = load  # type: ignore[attr-defined]
    toml_stub.loads = loads  # type: ignore[attr-defined]
    toml_stub.dump = dump  # type: ignore[attr-defined]
    toml_stub.dumps = dumps  # type: ignore[attr-defined]
    sys.modules["toml"] = toml_stub

if importlib.util.find_spec("yaml") is None:
    yaml_stub = types.ModuleType("yaml")

    def safe_load(
        stream: object,
    ) -> dict[str, object] | list[object] | None:  # pragma: no cover
        return {}

    def safe_dump(
        data: object, stream: object = None, *args: object, **kwargs: object
    ) -> str | None:  # pragma: no cover
        if stream is None:
            return ""
        return None

    yaml_stub.safe_load = safe_load  # type: ignore[attr-defined]
    yaml_stub.safe_dump = safe_dump  # type: ignore[attr-defined]
    sys.modules["yaml"] = yaml_stub

if importlib.util.find_spec("pydantic") is None:
    config_stub = types.ModuleType("devsynth.config")

    def load_project_config(
        path: object | None = None,
    ) -> dict[str, object]:  # pragma: no cover
        return {}

    def save_config(
        config: object, path: object | None = None
    ) -> None:  # pragma: no cover
        return None

    config_stub.load_project_config = load_project_config  # type: ignore[attr-defined]
    config_stub.save_config = save_config  # type: ignore[attr-defined]
    settings_stub = types.ModuleType("devsynth.config.settings")

    def ensure_path_exists(path: object) -> str:
        return str(path)

    settings_stub.ensure_path_exists = ensure_path_exists  # type: ignore[attr-defined]
    config_stub.settings = settings_stub  # type: ignore[attr-defined]
    sys.modules["devsynth.config"] = config_stub
    sys.modules["devsynth.config.settings"] = settings_stub

if importlib.util.find_spec("rich") is None:
    rich_module = types.ModuleType("rich")
    sys.modules["rich"] = rich_module

    rich_box = types.ModuleType("rich.box")
    rich_box.ROUNDED = object()  # type: ignore[attr-defined]
    rich_box.Box = object  # type: ignore[attr-defined]
    sys.modules["rich.box"] = rich_box

    class _Console:  # pragma: no cover - minimal stub
        def __init__(self, *args: object, **kwargs: object) -> None:
            return None

        def print(self, *_args: object, **_kwargs: object) -> None:
            return None

    rich_console = types.ModuleType("rich.console")
    rich_console.Console = _Console  # type: ignore[attr-defined]
    sys.modules["rich.console"] = rich_console

    class _Markdown:  # pragma: no cover - minimal stub
        def __init__(self, text: str, **_kwargs: object) -> None:
            self.text = text

    rich_markdown = types.ModuleType("rich.markdown")
    rich_markdown.Markdown = _Markdown  # type: ignore[attr-defined]
    sys.modules["rich.markdown"] = rich_markdown

    class _Panel:  # pragma: no cover - minimal stub
        def __init__(self, renderable: object, **_kwargs: object) -> None:
            self.renderable = renderable

    rich_panel = types.ModuleType("rich.panel")
    rich_panel.Panel = _Panel  # type: ignore[attr-defined]
    sys.modules["rich.panel"] = rich_panel

    rich_style = types.ModuleType("rich.style")
    rich_style.Style = object  # type: ignore[attr-defined]
    sys.modules["rich.style"] = rich_style

    class _Syntax:  # pragma: no cover - minimal stub
        def __init__(self, code: str, lexer: str, **_kwargs: object) -> None:
            self.code = code
            self.lexer = lexer

    rich_syntax = types.ModuleType("rich.syntax")
    rich_syntax.Syntax = _Syntax  # type: ignore[attr-defined]
    sys.modules["rich.syntax"] = rich_syntax

    class _Table:  # pragma: no cover - minimal stub
        def __init__(self, *args: object, **_kwargs: object) -> None:
            self.rows: list[tuple[object, ...]] = []

        def add_column(self, *_args: object, **_kwargs: object) -> None:
            return None

        def add_row(self, *cells: object) -> None:
            self.rows.append(tuple(cells))

    rich_table = types.ModuleType("rich.table")
    rich_table.Table = _Table  # type: ignore[attr-defined]
    sys.modules["rich.table"] = rich_table

    class _Text(str):  # pragma: no cover - minimal stub
        def __new__(cls, text: str, **_kwargs: object):
            return super().__new__(cls, text)

    rich_text = types.ModuleType("rich.text")
    rich_text.Text = _Text  # type: ignore[attr-defined]
    sys.modules["rich.text"] = rich_text

if importlib.util.find_spec("cryptography") is None:
    crypto_module = types.ModuleType("cryptography")
    sys.modules["cryptography"] = crypto_module

    fernet_module = types.ModuleType("cryptography.fernet")

    class Fernet:  # pragma: no cover - minimal stub
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return None

        @staticmethod
        def generate_key() -> bytes:
            return b"stub-key"

        def encrypt(self, data: bytes) -> bytes:
            return data

        def decrypt(self, token: bytes) -> bytes:
            return token

    fernet_module.Fernet = Fernet  # type: ignore[attr-defined]
    fernet_module.InvalidToken = Exception  # type: ignore[attr-defined]
    sys.modules["cryptography.fernet"] = fernet_module


import devsynth.interface.webui.rendering as rendering
from devsynth.interface.webui.rendering import ProjectSetupPages
from tests.unit.interface.test_webui_behavior_checklist_fast import (
    BehaviorStreamlitStub,
    ContainerRecorder,
)


class _Harness(ProjectSetupPages):
    """Project setup harness that records rendered messages."""

    def __init__(self, st: BehaviorStreamlitStub) -> None:
        self.streamlit = st
        self.messages: list[str] = []

    def display_result(self, message: str, **_kwargs: Any) -> None:
        self.messages.append(message)


class _FakeWizardState:
    def __init__(self, current_step: int, total_steps: int) -> None:
        self._current_step = current_step
        self._total_steps = total_steps

    def get_current_step(self) -> int:
        return self._current_step

    def get_total_steps(self) -> int:
        return self._total_steps


class _FakeWizardManager:
    def __init__(self) -> None:
        self._state = _FakeWizardState(3, 3)
        self.values: dict[str, Any] = {"wizard_started": True}
        self.reset_calls = 0
        self.cleared: list[tuple[str, ...]] = []
        self.completed = False

    def get_wizard_state(self) -> _FakeWizardState:
        return self._state

    def reset_wizard_state(self) -> bool:
        self.reset_calls += 1
        return True

    def clear_temporary_state(self, keys: list[str]) -> bool:
        self.cleared.append(tuple(keys))
        return True

    def set_value(self, key: str, value: Any) -> None:
        self.values[key] = value

    def get_value(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def set_completed(self, completed: bool = True) -> bool:
        self.completed = completed
        return True

    def next_step(self) -> bool:
        self._state._current_step = min(  # noqa: SLF001 - test stub
            self._state._total_steps,  # noqa: SLF001 - test stub
            self._state._current_step + 1,
        )
        return True

    def previous_step(self) -> bool:
        self._state._current_step = max(1, self._state._current_step - 1)
        return True


def _noop(
    self: ProjectSetupPages, wizard_state: Any
) -> None:  # noqa: ANN001 - test helper
    return None


def _always_valid(
    self: ProjectSetupPages, wizard_state: Any, step: int
) -> bool:  # noqa: ANN001 - test helper
    return True


@pytest.mark.fast
def test_gather_wizard_renders_cli_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    """The gather wizard mirrors CLI progress summaries with sanitized output."""

    frozen_now = 1_700_000_015.0
    monkeypatch.setattr(rendering.time, "time", lambda: frozen_now)
    monkeypatch.setattr(time, "time", lambda: frozen_now)

    stub = BehaviorStreamlitStub()
    stub.button = MagicMock(side_effect=[False, False, False, True])
    stub.columns = MagicMock(
        return_value=tuple(ContainerRecorder(stub, f"column[{i}]") for i in range(3))
    )
    stub.experimental_rerun = MagicMock()

    monkeypatch.setattr(rendering.ProjectSetupPages, "_handle_gather_step_1", _noop)
    monkeypatch.setattr(rendering.ProjectSetupPages, "_handle_gather_step_2", _noop)
    monkeypatch.setattr(rendering.ProjectSetupPages, "_handle_gather_step_3", _noop)
    monkeypatch.setattr(
        rendering.ProjectSetupPages, "_validate_gather_step", _always_valid
    )

    fake_manager = _FakeWizardManager()

    def fake_create_wizard_manager(
        _session_state: Any,
        _wizard_name: str,
        *,
        steps: int,
        initial_state: dict[str, Any] | None = None,
    ) -> _FakeWizardManager:
        assert steps == 3
        assert initial_state is not None
        return fake_manager

    monkeypatch.setattr(
        rendering.WebUIBridge,
        "create_wizard_manager",
        fake_create_wizard_manager,
    )

    eta_ts = frozen_now + 90.0
    fake_summary = {
        "description": "<Gather & Save>",
        "progress": 1.0,
        "elapsed": 42.0,
        "remaining_str": "0:00:00",
        "eta": eta_ts,
        "eta_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(eta_ts)),
        "history": [
            {"time": frozen_now - 10, "status": "Queued <init>", "completed": 0},
            {"time": frozen_now - 5, "status": "Collecting > sources", "completed": 50},
            {"time": frozen_now, "status": "Complete & verify", "completed": 100},
        ],
        "checkpoints": [
            {"time": frozen_now - 9, "progress": 0.25, "eta": eta_ts},
            {"time": frozen_now - 3, "progress": 0.75, "eta": eta_ts},
        ],
        "subtasks_detail": [
            {
                "description": "Docs <survey>",
                "progress": 1.0,
                "status": "Complete",
                "history": [
                    {
                        "time": frozen_now - 8,
                        "status": "Scanning & tagging",
                        "completed": 50,
                    },
                    {
                        "time": frozen_now - 6,
                        "status": "Summaries ready",
                        "completed": 100,
                    },
                ],
                "checkpoints": [
                    {"time": frozen_now - 7, "progress": 0.5, "eta": frozen_now - 2},
                ],
            },
            {
                "description": "Stakeholder interviews & analysis",
                "progress": 0.5,
                "status": "In progress",
                "history": [
                    {"time": frozen_now - 4, "status": "Scheduling", "completed": 20},
                ],
            },
        ],
    }

    gather_calls: list[ProjectSetupPages] = []

    def fake_gather(bridge: ProjectSetupPages) -> dict[str, Any]:
        gather_calls.append(bridge)
        return fake_summary

    monkeypatch.setattr(rendering, "gather_requirements", fake_gather)

    captured_run: dict[str, Any] = {}

    def fake_run_with_progress(
        task_name: str,
        task_fn,
        bridge: ProjectSetupPages,
        total: int = 100,
        subtasks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        captured_run.update(
            {
                "task_name": task_name,
                "bridge": bridge,
                "total": total,
                "subtasks": subtasks,
            }
        )
        return task_fn()

    monkeypatch.setattr(rendering, "run_with_progress", fake_run_with_progress)

    ui = _Harness(stub)
    ui._gather_wizard()

    expected_keys = (
        "resource_type_select",
        "resource_location_input",
        "metadata_author_input",
        "metadata_version_input",
        "metadata_tags_input",
        "metadata_doc_type_select",
        "metadata_language_select",
        "metadata_custom_field_name_input",
        "metadata_custom_field_value_input",
    )

    assert captured_run["task_name"] == "Processing resources..."
    assert captured_run["bridge"] is ui
    assert captured_run["total"] == 100
    assert captured_run["subtasks"] == [
        {"name": ui._get_gather_step_title(i), "total": 100} for i in range(1, 4)
    ]
    assert gather_calls == [ui]
    assert fake_manager.completed is True
    assert fake_manager.reset_calls == 1
    assert fake_manager.cleared == [expected_keys]
    assert stub.experimental_rerun.called
    assert ui.messages[-1] == "[green]Resources gathered successfully![/green]"

    assert len(stub.progress_bars) == 4
    wizard_bar, main_bar, docs_bar, interviews_bar = stub.progress_bars
    assert wizard_bar.values == [1.0]
    assert main_bar.values == [1.0]
    assert docs_bar.values == [1.0]
    assert interviews_bar.values == [0.5]

    assert len(stub.containers) == 5
    (
        main_container,
        history_container,
        checkpoints_container,
        docs_container,
        interviews_container,
    ) = stub.containers

    expected_eta = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(eta_ts))
    expected_eta_time = time.strftime("%H:%M:%S", time.localtime(eta_ts))
    assert (
        main_container.markdown_calls[0]
        == "**&lt;Gather &amp; Save&gt;** — 100% complete"
    )
    assert (
        main_container.info_calls[0]
        == f"ETA {expected_eta} (in 90s) • Remaining 0:00:00 • Elapsed 42s"
    )

    history_times = [
        time.strftime("%H:%M:%S", time.localtime(ts))
        for ts in (frozen_now - 10, frozen_now - 5, frozen_now)
    ]
    assert history_container.markdown_calls == [
        "**History**",
        f"- 0% • Queued &lt;init&gt; • {history_times[0]}",
        f"- 50% • Collecting &gt; sources • {history_times[1]}",
        f"- 100% • Complete &amp; verify • {history_times[2]}",
    ]

    checkpoint_times = [
        time.strftime("%H:%M:%S", time.localtime(ts))
        for ts in (frozen_now - 9, frozen_now - 3)
    ]
    assert checkpoints_container.markdown_calls == ["**Checkpoints**"]
    assert checkpoints_container.info_calls == [
        f"25% • {checkpoint_times[0]} • ETA {expected_eta_time} (in 90s)",
        f"75% • {checkpoint_times[1]} • ETA {expected_eta_time} (in 90s)",
    ]

    doc_history_times = [
        time.strftime("%H:%M:%S", time.localtime(ts))
        for ts in (frozen_now - 8, frozen_now - 6)
    ]
    assert docs_container.markdown_calls == [
        "**Docs &lt;survey&gt;** — 100% complete",
        "- Status: Complete",
        f"- 50% • Scanning &amp; tagging • {doc_history_times[0]}",
        f"- 100% • Summaries ready • {doc_history_times[1]}",
    ]
    doc_checkpoint_time = time.strftime("%H:%M:%S", time.localtime(frozen_now - 7))
    doc_eta_time = time.strftime("%H:%M:%S", time.localtime(frozen_now - 2))
    assert docs_container.info_calls == [
        f"50% • {doc_checkpoint_time} • ETA {doc_eta_time} (in 0s)"
    ]

    interview_history_time = time.strftime("%H:%M:%S", time.localtime(frozen_now - 4))
    assert interviews_container.markdown_calls == [
        "**Stakeholder interviews &amp; analysis** — 50% complete",
        "- Status: In progress",
        f"- 20% • Scheduling • {interview_history_time}",
    ]
    assert interviews_container.info_calls == []

    assert stub.button.call_count == 4


@pytest.mark.fast
def test_render_progress_summary_prefers_checkpoint_eta_strings() -> None:
    """Checkpoint rendering uses provided ETA labels instead of numeric fallback."""

    stub = BehaviorStreamlitStub()
    harness = _Harness(stub)

    summary = {
        "description": "<Daily run>",
        "progress": 0.5,
        "remaining": 12,
        "elapsed": 30,
        "checkpoints": [
            {
                "progress": 0.5,
                "eta_str": "T+5m",
            }
        ],
    }

    harness._render_progress_summary(summary)

    assert stub.containers[0].info_calls == ["Remaining 12s • Elapsed 30s"]
    assert stub.containers[1].markdown_calls == ["**Checkpoints**"]
    assert stub.containers[1].info_calls == ["50% • ETA T+5m"]
