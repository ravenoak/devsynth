from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytestmark = [pytest.mark.fast]


class _Slot:
    def __init__(self) -> None:
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []
        self.info_calls: list[str] = []
        self.empty_calls = 0
        self.success_calls: list[str] = []

    def markdown(self, text: str, **kwargs: object) -> None:
        self.markdown_calls.append((text, kwargs))

    def info(self, text: str) -> None:
        self.info_calls.append(text)

    def empty(self) -> None:
        self.empty_calls += 1

    def success(self, text: str) -> None:
        self.success_calls.append(text)


class _ProgressBar:
    def __init__(self) -> None:
        self.values: list[float] = []

    def progress(self, value: float) -> None:
        self.values.append(value)


class _Container:
    def __init__(self) -> None:
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []
        self.success_calls: list[str] = []
        self.progress_bars: list[_ProgressBar] = []

    def __enter__(self) -> _Container:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001
        return False

    def markdown(self, text: str, **kwargs: object) -> None:
        self.markdown_calls.append((text, kwargs))

    def progress(self, value: float) -> _ProgressBar:
        bar = _ProgressBar()
        bar.progress(value)
        self.progress_bars.append(bar)
        return bar

    def success(self, text: str) -> None:
        self.success_calls.append(text)


class StreamlitState(SimpleNamespace):
    markdown_calls: list[tuple[str, dict[str, object]]]
    error_messages: list[str]
    warning_messages: list[str]
    success_messages: list[str]
    info_messages: list[str]
    write_calls: list[str]
    slots: list[_Slot]
    progress_bars: list[_ProgressBar]
    containers: list[_Container]


def _make_streamlit_stub() -> tuple[ModuleType, StreamlitState]:
    state = StreamlitState(
        markdown_calls=[],
        error_messages=[],
        warning_messages=[],
        success_messages=[],
        info_messages=[],
        write_calls=[],
        slots=[],
        progress_bars=[],
        containers=[],
    )

    def markdown(text: str, **kwargs: object) -> None:
        state.markdown_calls.append((text, kwargs))

    def write(text: str, **kwargs: object) -> None:  # noqa: ARG001
        state.write_calls.append(text)

    def error(text: str) -> None:
        state.error_messages.append(text)

    def warning(text: str) -> None:
        state.warning_messages.append(text)

    def success(text: str) -> None:
        state.success_messages.append(text)

    def info(text: str) -> None:
        state.info_messages.append(text)

    def empty() -> _Slot:
        slot = _Slot()
        state.slots.append(slot)
        return slot

    def progress(value: float) -> _ProgressBar:
        bar = _ProgressBar()
        bar.progress(value)
        state.progress_bars.append(bar)
        return bar

    def container() -> _Container:
        ctx = _Container()
        state.containers.append(ctx)
        return ctx

    streamlit = ModuleType("streamlit")
    streamlit.session_state = {}
    streamlit.sidebar = SimpleNamespace(title=MagicMock(), markdown=MagicMock())
    streamlit.components = SimpleNamespace(v1=SimpleNamespace(html=MagicMock()))
    streamlit.markdown = markdown
    streamlit.write = write
    streamlit.error = error
    streamlit.warning = warning
    streamlit.success = success
    streamlit.info = info
    streamlit.empty = empty
    streamlit.progress = progress
    streamlit.container = container
    streamlit.checkbox = MagicMock()
    streamlit.text_input = MagicMock()
    streamlit.selectbox = MagicMock()
    streamlit.set_page_config = MagicMock()
    streamlit.header = MagicMock()
    streamlit.subheader = MagicMock()
    streamlit.expander = MagicMock(side_effect=lambda *_, **__: container())

    return streamlit, state


@pytest.fixture
def webui_module(monkeypatch: pytest.MonkeyPatch):
    streamlit_mod, state = _make_streamlit_stub()
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_mod)
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())
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
    config_stub = ModuleType("devsynth.config")
    config_stub.load_project_config = MagicMock(return_value={})
    config_stub.save_config = MagicMock()
    monkeypatch.setitem(sys.modules, "devsynth.config", config_stub)
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
            self.args = args
            self.kwargs = kwargs
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
    sys.modules.pop("devsynth.interface.webui", None)
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    monkeypatch.setattr(webui, "sanitize_output", lambda text: text)
    return webui, state


def test_display_result_translates_markup_to_markdown(webui_module):
    webui, state = webui_module
    ui = webui.WebUI()

    ui.display_result("[bold]Done[/bold] [green]ok[/green]")

    assert state.markdown_calls, "markdown() should be used for rich output"
    rendered, kwargs = state.markdown_calls[-1]
    assert "**Done**" in rendered
    assert '<span style="color:green">ok</span>' in rendered
    assert kwargs.get("unsafe_allow_html") is True


def test_display_result_surfaces_guidance_for_file_errors(webui_module):
    webui, state = webui_module
    ui = webui.WebUI()

    ui.display_result("ERROR: File not found: missing.txt", message_type="error")

    assert state.error_messages[-1] == "ERROR: File not found: missing.txt"
    rendered_sections = [payload for payload, _ in state.markdown_calls]
    assert any("Suggestions" in section for section in rendered_sections)
    assert any("Documentation" in section for section in rendered_sections)
    assert any("File Handling Guide" in section for section in rendered_sections)


def test_display_result_highlights_information(webui_module):
    webui, state = webui_module
    ui = webui.WebUI()

    ui.display_result("Important details", highlight=True)

    assert state.info_messages[-1] == "Important details"


def test_ui_progress_tracks_status_and_subtasks(webui_module, monkeypatch):
    webui, state = webui_module
    ui = webui.WebUI()

    time_values = iter([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
    monkeypatch.setattr(webui.time, "time", lambda: next(time_values))

    progress = ui.create_progress("Primary task", total=4)
    assert pytest.approx(state.progress_bars[0].values[0]) == 0.0

    progress.update(advance=2)
    assert pytest.approx(state.progress_bars[0].values[-1]) == 0.5
    assert "**Primary task**" in state.slots[0].markdown_calls[-1][0]

    subtask_id = progress.add_subtask("Subtask", total=2)
    container = state.containers[-1]
    assert container.markdown_calls[-1][0].endswith("0%")

    progress.update_subtask(subtask_id, advance=1, description="Halfway there")
    assert "Halfway there" in container.markdown_calls[-1][0]

    progress.complete_subtask(subtask_id)
    assert container.success_calls[-1].startswith("Completed:")

    progress.complete()
    assert pytest.approx(state.progress_bars[0].values[-1]) == 1.0
    assert state.success_messages[-1] == "Completed: Primary task"
