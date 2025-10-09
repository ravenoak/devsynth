from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytestmark = [pytest.mark.fast]


def _install_nicegui_stub(monkeypatch: pytest.MonkeyPatch):
    labels: list[SimpleNamespace] = []
    bars: list[SimpleNamespace] = []

    class RowContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def classes(self, *_):
            return self

    def make_label(text: str) -> SimpleNamespace:
        label = SimpleNamespace(text=text)
        labels.append(label)
        return label

    def make_progress(value: float = 0.0) -> SimpleNamespace:
        bar = SimpleNamespace(value=value)
        bars.append(bar)
        return bar

    ui_stub = SimpleNamespace(
        row=lambda: RowContext(),
        label=make_label,
        linear_progress=make_progress,
        notify=MagicMock(),
    )

    app_stub = SimpleNamespace(storage=SimpleNamespace(user={}))

    nicegui_module = ModuleType("nicegui")
    nicegui_module.ui = ui_stub
    nicegui_module.app = app_stub

    previous_nicegui = sys.modules.get("nicegui")
    previous_webui = sys.modules.get("devsynth.interface.nicegui_webui")
    monkeypatch.setitem(sys.modules, "nicegui", nicegui_module)
    security_pkg = ModuleType("devsynth.security")
    security_pkg.__path__ = []  # type: ignore[attr-defined]
    validation_stub = ModuleType("devsynth.security.validation")
    validation_stub.parse_bool_env = lambda _name, default=True: default
    sanitization_stub = ModuleType("devsynth.security.sanitization")
    sanitization_stub.sanitize_input = lambda text: text
    auth_stub = ModuleType("devsynth.security.authentication")
    auth_stub.authenticate = MagicMock(return_value=True)
    auth_stub.hash_password = MagicMock(return_value="hash")
    auth_stub.verify_password = MagicMock(return_value=True)
    monkeypatch.setitem(sys.modules, "devsynth.security", security_pkg)
    monkeypatch.setitem(sys.modules, "devsynth.security.validation", validation_stub)
    monkeypatch.setitem(
        sys.modules, "devsynth.security.sanitization", sanitization_stub
    )
    monkeypatch.setitem(sys.modules, "devsynth.security.authentication", auth_stub)
    security_pkg.validation = validation_stub
    security_pkg.sanitization = sanitization_stub
    security_pkg.authentication = auth_stub
    monkeypatch.setitem(sys.modules, "yaml", MagicMock())
    rich_module = ModuleType("rich")
    rich_box = ModuleType("rich.box")
    rich_box.ROUNDED = MagicMock()
    rich_box.Box = MagicMock()
    rich_console = ModuleType("rich.console")

    class _Console:
        def __init__(self, *args, **kwargs):
            self.print_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

        def print(self, *args, **kwargs):
            self.print_calls.append((args, kwargs))

    rich_console.Console = _Console
    rich_markdown = ModuleType("rich.markdown")

    class _Markdown:
        def __init__(self, text: str, **kwargs: object) -> None:
            self.text = text
            self.kwargs = kwargs

    rich_markdown.Markdown = _Markdown
    rich_panel = ModuleType("rich.panel")

    class _Panel:
        def __init__(self, renderable: object, **kwargs: object) -> None:
            self.renderable = renderable
            self.kwargs = kwargs

    rich_panel.Panel = _Panel
    rich_style = ModuleType("rich.style")

    class _Style:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

    rich_style.Style = _Style
    rich_syntax = ModuleType("rich.syntax")

    class _Syntax:
        def __init__(
            self, code: str, lexer: str | None = None, **kwargs: object
        ) -> None:
            self.code = code
            self.lexer = lexer
            self.kwargs = kwargs

    rich_syntax.Syntax = _Syntax
    rich_table = ModuleType("rich.table")

    class _Table:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.columns: list[tuple[str, dict[str, object]]] = []
            self.rows: list[tuple[tuple[object, ...], dict[str, object]]] = []

        def add_column(self, name: str, **kwargs: object) -> None:
            self.columns.append((name, kwargs))

        def add_row(self, *cells: object, **kwargs: object) -> None:
            self.rows.append((cells, kwargs))

    rich_table.Table = _Table
    rich_text = ModuleType("rich.text")

    class _Text(str):
        def __new__(cls, text: str, *args: object, **kwargs: object):  # type: ignore[override]
            obj = str.__new__(cls, text)
            obj._args = args  # type: ignore[attr-defined]
            obj._kwargs = kwargs  # type: ignore[attr-defined]
            return obj

    rich_text.Text = _Text
    rich_module.box = rich_box
    rich_module.console = rich_console
    rich_module.markdown = rich_markdown
    rich_module.panel = rich_panel
    rich_module.style = rich_style
    rich_module.syntax = rich_syntax
    rich_module.table = rich_table
    rich_module.text = rich_text
    monkeypatch.setitem(sys.modules, "rich", rich_module)
    monkeypatch.setitem(sys.modules, "rich.box", rich_box)
    monkeypatch.setitem(sys.modules, "rich.console", rich_console)
    monkeypatch.setitem(sys.modules, "rich.markdown", rich_markdown)
    monkeypatch.setitem(sys.modules, "rich.panel", rich_panel)
    monkeypatch.setitem(sys.modules, "rich.style", rich_style)
    monkeypatch.setitem(sys.modules, "rich.syntax", rich_syntax)
    monkeypatch.setitem(sys.modules, "rich.table", rich_table)
    monkeypatch.setitem(sys.modules, "rich.text", rich_text)

    import devsynth.interface.nicegui_webui as nicegui_webui

    importlib.reload(nicegui_webui)
    nicegui_webui._session_store.clear()

    def cleanup() -> None:
        nicegui_webui._session_store.clear()
        if previous_nicegui is not None:
            sys.modules["nicegui"] = previous_nicegui
        else:
            sys.modules.pop("nicegui", None)
        if previous_webui is not None:
            sys.modules["devsynth.interface.nicegui_webui"] = previous_webui
        else:
            sys.modules.pop("devsynth.interface.nicegui_webui", None)

    return nicegui_webui, ui_stub, labels, bars, cleanup


@pytest.fixture
def nicegui_setup(monkeypatch: pytest.MonkeyPatch):
    module, ui_stub, labels, bars, cleanup = _install_nicegui_stub(monkeypatch)
    try:
        yield module, ui_stub, labels, bars
    finally:
        cleanup()


def test_session_storage_roundtrip(nicegui_setup):
    module, _, _, _ = nicegui_setup
    bridge = module.NiceGUIBridge()
    bridge.set_session_value("key", "value")
    assert bridge.get_session_value("key") == "value"


def test_display_result_notifies_and_records(nicegui_setup):
    module, ui_stub, _, _ = nicegui_setup
    bridge = module.NiceGUIBridge()

    bridge.display_result("[bold]Completed[/bold]", message_type="success")

    ui_stub.notify.assert_called_once()
    assert any("Completed" in message for message in bridge.messages)


def test_progress_indicator_updates_and_completes(nicegui_setup):
    module, _, labels, bars = nicegui_setup
    bridge = module.NiceGUIBridge()

    indicator = bridge.create_progress("Task", total=4)
    indicator.update(advance=2, description="Working")

    assert labels[-1].text == module.sanitize_output("Working")
    assert pytest.approx(bars[-1].value) == 0.5

    indicator.complete()
    assert pytest.approx(bars[-1].value) == 1.0


def test_display_result_falls_back_without_nicegui(monkeypatch, nicegui_setup):
    module, ui_stub, _, _ = nicegui_setup
    monkeypatch.setattr(module, "_HAS_NICEGUI", False, raising=False)
    bridge = module.NiceGUIBridge()

    bridge.display_result("Plain text", message_type="info")

    assert ui_stub.notify.call_count == 0
    assert bridge.messages[-1] == "Plain text"
