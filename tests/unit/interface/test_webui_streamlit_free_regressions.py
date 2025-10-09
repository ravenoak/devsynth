"""Streamlit-free regression tests for WebUI modules."""

from __future__ import annotations

import importlib
import sys
import types
from collections.abc import Iterable

import pytest


class _DummyPasswordHasher:
    def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - lightweight stub
        """Accept arbitrary initialization parameters."""

    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, stored_hash: str, password: str) -> bool:
        return stored_hash == self.hash(password)


argon2_module = types.ModuleType("argon2")
argon2_module.PasswordHasher = _DummyPasswordHasher  # type: ignore[attr-defined]
sys.modules.setdefault("argon2", argon2_module)

argon2_exceptions = types.ModuleType("argon2.exceptions")
argon2_exceptions.VerifyMismatchError = Exception  # type: ignore[attr-defined]
sys.modules.setdefault("argon2.exceptions", argon2_exceptions)

jsonschema_module = types.ModuleType("jsonschema")


class _ValidationError(Exception):
    pass


class _SchemaError(Exception):
    pass


def _noop_validate(*_: object, **__: object) -> None:
    return None


jsonschema_module.validate = _noop_validate  # type: ignore[attr-defined]
jsonschema_exceptions = types.ModuleType("jsonschema.exceptions")
jsonschema_exceptions.ValidationError = _ValidationError  # type: ignore[attr-defined]
jsonschema_exceptions.SchemaError = _SchemaError  # type: ignore[attr-defined]
jsonschema_module.exceptions = jsonschema_exceptions  # type: ignore[attr-defined]
sys.modules.setdefault("jsonschema", jsonschema_module)
sys.modules.setdefault("jsonschema.exceptions", jsonschema_exceptions)

yaml_module = types.ModuleType("yaml")
yaml_module.safe_load = lambda data: {}  # type: ignore[attr-defined]
sys.modules.setdefault("yaml", yaml_module)

toml_module = types.ModuleType("toml")
toml_module.load = lambda *args, **kwargs: {}  # type: ignore[attr-defined]
toml_module.dump = lambda *args, **kwargs: None  # type: ignore[attr-defined]
toml_module.TomlDecodeError = Exception  # type: ignore[attr-defined]
sys.modules.setdefault("toml", toml_module)

pydantic_module = types.ModuleType("pydantic")
pydantic_module.ValidationError = Exception  # type: ignore[attr-defined]
pydantic_module.Field = (  # type: ignore[attr-defined]
    lambda *args, default=None, default_factory=None, **kwargs: (
        default_factory() if default_factory is not None else default
    )
)
pydantic_module.FieldValidationInfo = type(
    "FieldValidationInfo",
    (object,),
    {"field_name": "", "data": {}},
)  # type: ignore[attr-defined]


def _field_validator(*_args, **_kwargs):  # type: ignore[override]
    def decorator(func):
        return func

    return decorator


pydantic_module.field_validator = _field_validator  # type: ignore[attr-defined]
sys.modules.setdefault("pydantic", pydantic_module)

from dataclasses import dataclass as _std_dataclass

pydantic_dataclasses = types.ModuleType("pydantic.dataclasses")
pydantic_dataclasses.dataclass = _std_dataclass  # type: ignore[attr-defined]
sys.modules.setdefault("pydantic.dataclasses", pydantic_dataclasses)

pydantic_settings_module = types.ModuleType("pydantic_settings")


class _BaseSettings:
    model_config: dict[str, object] = {}


pydantic_settings_module.BaseSettings = _BaseSettings  # type: ignore[attr-defined]
pydantic_settings_module.SettingsConfigDict = dict  # type: ignore[attr-defined]
sys.modules.setdefault("pydantic_settings", pydantic_settings_module)

commands_stub = types.ModuleType("devsynth.interface.webui.commands")


def _noop_command(*_args, **_kwargs) -> None:
    return None


commands_stub.__all__ = ["noop_command"]  # type: ignore[attr-defined]
commands_stub.noop_command = _noop_command  # type: ignore[attr-defined]
sys.modules["devsynth.interface.webui.commands"] = commands_stub

rendering_stub = types.ModuleType("devsynth.interface.webui.rendering")


class _StubPageRenderer:
    def __init__(self, *args, **kwargs) -> None:  # noqa: D401
        pass

    def navigation_items(self) -> list[str]:
        return []


rendering_stub.PageRenderer = _StubPageRenderer  # type: ignore[attr-defined]
sys.modules["devsynth.interface.webui.rendering"] = rendering_stub

routing_stub = types.ModuleType("devsynth.interface.webui.routing")


class _StubRouter:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def run(self) -> None:
        return None


routing_stub.Router = _StubRouter  # type: ignore[attr-defined]
sys.modules["devsynth.interface.webui.routing"] = routing_stub

rich_module = types.ModuleType("rich")
sys.modules.setdefault("rich", rich_module)

rich_box = types.ModuleType("rich.box")
rich_box.ROUNDED = object()  # type: ignore[attr-defined]
rich_box.Box = object  # type: ignore[attr-defined]
sys.modules.setdefault("rich.box", rich_box)


class _Console:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def print(self, *args, **kwargs) -> None:
        return None


rich_console = types.ModuleType("rich.console")
rich_console.Console = _Console  # type: ignore[attr-defined]
sys.modules.setdefault("rich.console", rich_console)


class _Markdown:
    def __init__(self, text: str, *_, **__) -> None:
        self.text = text


rich_markdown = types.ModuleType("rich.markdown")
rich_markdown.Markdown = _Markdown  # type: ignore[attr-defined]
sys.modules.setdefault("rich.markdown", rich_markdown)


class _Panel:
    def __init__(self, renderable: object, *_, **__) -> None:
        self.renderable = renderable


rich_panel = types.ModuleType("rich.panel")
rich_panel.Panel = _Panel  # type: ignore[attr-defined]
sys.modules.setdefault("rich.panel", rich_panel)

rich_style = types.ModuleType("rich.style")
rich_style.Style = object  # type: ignore[attr-defined]
sys.modules.setdefault("rich.style", rich_style)


class _Syntax:
    def __init__(self, code: str, *_, **__) -> None:
        self.code = code


rich_syntax = types.ModuleType("rich.syntax")
rich_syntax.Syntax = _Syntax  # type: ignore[attr-defined]
sys.modules.setdefault("rich.syntax", rich_syntax)


class _Table:
    def __init__(self, *_, **__) -> None:
        self.columns: list[str] = []
        self.rows: list[list[object]] = []

    def add_column(self, name: str, *_, **__) -> None:
        self.columns.append(name)

    def add_row(self, *values: object, **__) -> None:
        self.rows.append(list(values))


rich_table = types.ModuleType("rich.table")
rich_table.Table = _Table  # type: ignore[attr-defined]
sys.modules.setdefault("rich.table", rich_table)


class _Text(str):
    def __new__(cls, value: str, *_, **__):
        return super().__new__(cls, value)


rich_text = types.ModuleType("rich.text")
rich_text.Text = _Text  # type: ignore[attr-defined]
sys.modules.setdefault("rich.text", rich_text)

from devsynth.exceptions import DevSynthError
from devsynth.interface import webui, webui_bridge


class _RecordingStreamlit:
    """Minimal Streamlit stub that records routed messages."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.info_calls: list[str] = []
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []

    def error(self, message: str) -> None:
        self.calls.append(("error", message))

    def warning(self, message: str) -> None:
        self.calls.append(("warning", message))

    def success(self, message: str) -> None:
        self.calls.append(("success", message))

    def info(self, message: str) -> None:
        self.calls.append(("info", message))
        self.info_calls.append(message)

    def write(self, message: str) -> None:
        self.calls.append(("write", message))

    def markdown(self, message: str, **kwargs: object) -> None:
        self.markdown_calls.append((message, kwargs))


class _FakeProgressBar:
    def __init__(self) -> None:
        self.progress_values: list[float] = []

    def progress(self, value: float) -> None:
        self.progress_values.append(value)


class _FakeStatusContainer:
    def __init__(self) -> None:
        self.markdowns: list[str] = []

    def markdown(self, message: str, **_: object) -> None:
        self.markdowns.append(message)


class _FakeTimeContainer:
    def __init__(self) -> None:
        self.infos: list[str] = []
        self.emptied: int = 0

    def info(self, message: str, **_: object) -> None:
        self.infos.append(message)

    def empty(self) -> None:
        self.emptied += 1


class _FakeContainer:
    def __init__(self) -> None:
        self.markdowns: list[str] = []
        self.success_messages: list[str] = []
        self.progress_bar = _FakeProgressBar()

    def __enter__(self) -> "_FakeContainer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None

    def markdown(self, message: str, **_: object) -> None:
        self.markdowns.append(message)

    def success(self, message: str, **_: object) -> None:
        self.success_messages.append(message)

    def progress(self, value: float, **_: object) -> _FakeProgressBar:
        self.progress_bar.progress(value)
        return self.progress_bar


class _WebUIStreamlitStub(_RecordingStreamlit):
    def __init__(self) -> None:
        super().__init__()
        self.status_container = _FakeStatusContainer()
        self.time_container = _FakeTimeContainer()
        self.containers: list[_FakeContainer] = []
        self.progress_bars: list[_FakeProgressBar] = []
        self._empty_calls = 0

    def empty(self) -> object:
        self._empty_calls += 1
        if self._empty_calls == 1:
            return self.status_container
        return self.time_container

    def progress(self, value: float, **_: object) -> _FakeProgressBar:
        bar = _FakeProgressBar()
        bar.progress(value)
        self.progress_bars.append(bar)
        return bar

    def container(self) -> _FakeContainer:
        container = _FakeContainer()
        self.containers.append(container)
        return container


def _time_generator(values: Iterable[float]) -> callable:
    iterator = iter(values)

    def _next_time() -> float:
        try:
            return next(iterator)
        except StopIteration:
            # Reuse the last value if calls exceed the provided sequence.
            return values[-1]  # type: ignore[index]

    return _next_time


@pytest.mark.fast
def test_webui_require_streamlit_reports_install_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing Streamlit surfaces actionable guidance."""

    monkeypatch.setattr(webui, "_STREAMLIT", None)

    def _raise(_: str) -> None:
        raise ImportError("streamlit not available")

    monkeypatch.setattr(importlib, "import_module", _raise)

    with pytest.raises(DevSynthError) as exc:
        webui._require_streamlit()

    message = str(exc.value)
    assert "Streamlit is required to use the DevSynth WebUI." in message
    assert "poetry install --with dev --extras webui" in message


@pytest.mark.fast
def test_webui_bridge_require_streamlit_reports_install_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bridge also surfaces the install command when Streamlit is unavailable."""

    monkeypatch.setattr(webui_bridge, "st", None, raising=False)

    def _raise(_: str) -> None:
        raise ModuleNotFoundError("streamlit missing")

    monkeypatch.setattr(importlib, "import_module", _raise)

    with pytest.raises(DevSynthError) as exc:
        webui_bridge._require_streamlit()

    message = str(exc.value)
    assert "Streamlit is required for WebUI features" in message
    assert "poetry install --with dev --extras webui" in message


@pytest.mark.fast
@pytest.mark.parametrize(
    ("branch", "kwargs", "expected_method"),
    [
        ("error", {"message_type": "error"}, "error"),
        ("warning", {"message_type": "warning"}, "warning"),
        ("success", {"message_type": "success"}, "success"),
        ("highlight", {"highlight": True}, "info"),
    ],
)
def test_webui_display_result_sanitizes_without_streamlit(
    monkeypatch: pytest.MonkeyPatch,
    branch: str,
    kwargs: dict[str, object],
    expected_method: str,
) -> None:
    """`WebUI.display_result` routes sanitized text through the stubbed Streamlit API."""

    stub = _WebUIStreamlitStub()
    monkeypatch.setattr(webui, "_STREAMLIT", stub)
    ui = webui.WebUI()

    payload = "<script>unsafe</script>"
    ui.display_result(payload, **kwargs)

    assert stub.calls, "display_result did not reach the Streamlit stub"
    method, message = stub.calls[0]
    assert method == expected_method
    assert message != payload
    assert "<" not in message


@pytest.mark.fast
@pytest.mark.parametrize(
    ("branch", "kwargs", "expected_method"),
    [
        ("error", {"message_type": "error"}, "error"),
        ("warning", {"message_type": "warning"}, "warning"),
        ("success", {"message_type": "success"}, "success"),
        ("highlight", {"highlight": True}, "info"),
    ],
)
def test_webui_bridge_display_result_sanitizes_without_streamlit(
    monkeypatch: pytest.MonkeyPatch,
    branch: str,
    kwargs: dict[str, object],
    expected_method: str,
) -> None:
    """`WebUIBridge.display_result` sanitizes messages before delegating to Streamlit."""

    stub = _RecordingStreamlit()
    monkeypatch.setattr(webui_bridge, "st", stub, raising=False)
    bridge = webui_bridge.WebUIBridge()

    payload = "<div>unsafe</div>"
    bridge.display_result(payload, **kwargs)  # type: ignore[arg-type]

    assert stub.calls, "display_result did not forward to the stub"
    method, message = stub.calls[0]
    assert method == expected_method
    rendered = getattr(message, "renderable", message)
    assert payload not in str(rendered)
    assert payload not in str(
        getattr(bridge.messages[-1], "renderable", bridge.messages[-1])
    )


@pytest.mark.fast
def test_webui_progress_indicator_nested_lifecycle_and_statuses() -> None:
    """Nested subtask lifecycle updates remain sanitized and consistent."""

    indicator = webui_bridge.WebUIProgressIndicator("Top Level", total=100)

    indicator.update(advance=25)
    assert indicator._status == "Starting..."

    indicator.update(description="<b>phase</b>", status=None)
    assert indicator._description == "&lt;b&gt;phase&lt;/b&gt;"
    assert indicator._status == "Processing..."

    sub_id = indicator.add_subtask("Phase <1>", total=10)
    nested_id = indicator.add_nested_subtask(sub_id, "Nested <A>", total=4)

    indicator.update_subtask(sub_id, advance=5)
    subtask = indicator._subtasks[sub_id]
    assert subtask.description == "Phase &lt;1&gt;"
    assert subtask.status == "Halfway there..."

    indicator.update_nested_subtask(sub_id, nested_id, advance=2)
    nested = subtask.nested_subtasks[nested_id]
    assert nested.description == "Nested &lt;A&gt;"
    assert nested.status == "Starting..."

    indicator.complete_nested_subtask(sub_id, nested_id)
    assert nested.completed is True
    assert nested.status == "Complete"

    indicator.complete_subtask(sub_id)
    assert subtask.completed is True
    assert subtask.status == "Complete"

    indicator.complete()
    assert indicator._current == indicator._total


@pytest.mark.fast
@pytest.mark.parametrize(
    ("current", "total", "expected"),
    [
        (0, 0, "Starting..."),
        (10, 100, "Starting..."),
        (25, 100, "Processing..."),
        (50, 100, "Halfway there..."),
        (80, 100, "Almost done..."),
        (99, 100, "Finalizing..."),
        (100, 100, "Complete"),
    ],
)
def test_default_status_thresholds(current: float, total: int, expected: str) -> None:
    """`_default_status` clamps thresholds deterministically."""

    assert webui_bridge._default_status(current, total) == expected


@pytest.mark.fast
def test_webui_ui_progress_eta_formats(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Streamlit UI progress indicator formats ETA strings across ranges."""

    stub = _WebUIStreamlitStub()
    monkeypatch.setattr(webui, "_STREAMLIT", stub)

    times = [0.0, 0.5, 5.0, 3605.0, 39605.0]
    monkeypatch.setattr(webui.time, "time", _time_generator(times))

    progress = webui.WebUI().create_progress("Build <Task>", total=100)

    progress.update(advance=25)
    progress.update(advance=50)
    progress.update(advance=1)

    assert stub.time_container.infos == [
        "ETA: 13 seconds",
        "ETA: 20 minutes",
        "ETA: 3 hours, 28 minutes",
    ]
    assert stub.progress_bars[0].progress_values[-1] == pytest.approx(0.76, rel=1e-6)


@pytest.mark.fast
def test_wizard_helpers_clamp_malformed_inputs() -> None:
    """Wizard helpers coerce malformed navigation requests into range."""

    next_step = webui_bridge.WebUIBridge.adjust_wizard_step(
        "2", direction="next", total=0
    )
    assert next_step == 0

    back_step = webui_bridge.WebUIBridge.adjust_wizard_step(
        0, direction="back", total=1
    )
    assert back_step == 0

    same_step = webui_bridge.WebUIBridge.adjust_wizard_step(
        5, direction="stay", total=3
    )
    assert same_step == 2

    normalized = webui_bridge.WebUIBridge.normalize_wizard_step(" 4.7 ", total=3)
    assert normalized == 2

    normalized_invalid = webui_bridge.WebUIBridge.normalize_wizard_step(
        "not-a-number", total=4
    )
    assert normalized == 2
    assert normalized_invalid == 0
