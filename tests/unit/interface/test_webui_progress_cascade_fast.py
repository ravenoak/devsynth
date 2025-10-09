"""Fast tests validating WebUI progress cascades and sanitized fallbacks."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from devsynth.interface import webui

pytestmark = pytest.mark.fast


class _StubBlock:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[tuple[str, object]] = []

    def markdown(self, message: str) -> None:
        self.calls.append(("markdown", message))

    def info(self, message: str) -> None:
        self.calls.append(("info", message))

    def empty(self) -> None:
        self.calls.append(("empty", None))


class _StubProgressBar:
    def __init__(self, owner: "_StubSubtask" | None = None) -> None:
        self._owner = owner
        self.values: list[float] = []

    def progress(self, value: float) -> None:
        self.values.append(value)
        if self._owner is not None:
            self._owner.progress_updates.append(value)


class _StubSubtask:
    def __init__(self) -> None:
        self.markdown_calls: list[str] = []
        self.success_calls: list[str] = []
        self.progress_updates: list[float] = []
        self.progress_bar = _StubProgressBar(self)

    def markdown(self, text: str) -> None:
        self.markdown_calls.append(text)

    def progress(self, value: float) -> _StubProgressBar:
        self.progress_bar.progress(value)
        return self.progress_bar

    def success(self, message: str) -> None:
        self.success_calls.append(message)


class _ContainerContext:
    def __init__(self, subtask: _StubSubtask) -> None:
        self._subtask = subtask

    def __enter__(self) -> _StubSubtask:
        return self._subtask

    def __exit__(
        self, exc_type, exc, tb
    ) -> None:  # noqa: D401, ANN001 - pytest fixture pattern
        return None


class _StubExpander:
    def __init__(self, label: str) -> None:
        self.label = label
        self.records: list[tuple[str, object]] = []

    def __enter__(self) -> "_StubExpander":
        return self

    def __exit__(
        self, exc_type, exc, tb
    ) -> None:  # noqa: D401, ANN001 - pytest fixture pattern
        return None

    def code(self, text: str, *, language: str | None = None) -> None:
        self.records.append(("code", {"text": text, "language": language}))


class _SessionState(dict[str, object]):
    def __init__(self, **initial: object) -> None:
        super().__init__(initial)

    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - defensive attr access
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


class _StubSidebar:
    def __init__(self) -> None:
        self.title_calls: list[str] = []
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []

    def title(self, message: str) -> None:
        self.title_calls.append(message)

    def markdown(self, message: str, **kwargs: object) -> None:
        self.markdown_calls.append((message, kwargs))


class _StubComponents:
    def __init__(self, owner: "_StubStreamlit") -> None:
        self._owner = owner
        self.calls: list[dict[str, object]] = []
        self.v1 = SimpleNamespace(html=self._html)

    def _html(self, code: str, *, height: int = 0) -> None:
        if self._owner.raise_html_error:
            raise RuntimeError("html failure")
        self.calls.append({"code": code, "height": height})


class _StubStreamlit:
    def __init__(self) -> None:
        self.session_state = _SessionState(screen_width=1200)
        self._empty_calls = 0
        self.status_blocks: list[_StubBlock] = []
        self.time_blocks: list[_StubBlock] = []
        self.progress_bars: list[_StubProgressBar] = []
        self.subtasks: list[_StubSubtask] = []
        self.write_messages: list[str] = []
        self.markdown_messages: list[tuple[str, dict[str, object]]] = []
        self.info_messages: list[str] = []
        self.warning_messages: list[str] = []
        self.error_messages: list[str] = []
        self.success_messages: list[str] = []
        self.headers: list[str] = []
        self.subheaders: list[str] = []
        self.code_blocks: list[dict[str, object]] = []
        self.selectbox_calls: list[dict[str, object]] = []
        self.text_input_calls: list[dict[str, object]] = []
        self.checkbox_calls: list[dict[str, object]] = []
        self.expanders: list[_StubExpander] = []
        self._allow_info = True
        self._allow_success = True
        self.raise_page_config = False
        self.raise_html_error = False
        self.set_page_config_calls: list[dict[str, object]] = []
        self.components = _StubComponents(self)
        self.sidebar = _StubSidebar()

    def __getattr__(self, name: str):  # pragma: no cover - simple attribute fallback
        if name == "info":
            if self._allow_info:
                return self._info
            raise AttributeError(name)
        if name == "success":
            if self._allow_success:
                return self._success
            raise AttributeError(name)
        raise AttributeError(name)

    def _info(self, message: str) -> None:
        self.info_messages.append(message)

    def _success(self, message: str) -> None:
        self.success_messages.append(message)

    def empty(self) -> _StubBlock:
        block = _StubBlock(f"block_{self._empty_calls}")
        if self._empty_calls == 0:
            self.status_blocks.append(block)
        else:
            self.time_blocks.append(block)
        self._empty_calls += 1
        return block

    def progress(self, initial: float) -> _StubProgressBar:
        bar = _StubProgressBar()
        bar.progress(initial)
        self.progress_bars.append(bar)
        return bar

    def container(self) -> _ContainerContext:
        subtask = _StubSubtask()
        self.subtasks.append(subtask)
        return _ContainerContext(subtask)

    def write(self, message: str) -> None:
        self.write_messages.append(message)

    def markdown(self, message: str, **kwargs: object) -> None:
        self.markdown_messages.append((message, kwargs))

    def warning(self, message: str) -> None:
        self.warning_messages.append(message)

    def error(self, message: str) -> None:
        self.error_messages.append(message)

    def header(self, message: str) -> None:
        self.headers.append(message)

    def subheader(self, message: str) -> None:
        self.subheaders.append(message)

    def selectbox(
        self, message: str, choices: list[str], *, index: int, key: str
    ) -> str:
        record = {
            "message": message,
            "choices": list(choices),
            "index": index,
            "key": key,
        }
        self.selectbox_calls.append(record)
        return record["choices"][index]

    def code(self, text: str, *, language: str | None = None) -> None:
        self.code_blocks.append({"text": text, "language": language})

    def text_input(self, message: str, *, value: str, key: str) -> str:
        record = {"message": message, "value": value, "key": key}
        self.text_input_calls.append(record)
        return value

    def checkbox(self, message: str, *, value: bool, key: str) -> bool:
        record = {"message": message, "value": value, "key": key}
        self.checkbox_calls.append(record)
        return value

    def expander(self, label: str) -> _StubExpander:
        expander = _StubExpander(label)
        self.expanders.append(expander)
        return expander

    def set_page_config(self, *, page_title: str, layout: str) -> None:
        if self.raise_page_config:
            raise RuntimeError("set_page_config failure")
        self.set_page_config_calls.append({"page_title": page_title, "layout": layout})


@pytest.fixture()
def streamlit_stub(monkeypatch: pytest.MonkeyPatch) -> _StubStreamlit:
    stub = _StubStreamlit()
    monkeypatch.setattr(webui, "st", stub)
    return stub


def test_progress_complete_cascades_with_sanitized_fallback(
    streamlit_stub: _StubStreamlit, monkeypatch: pytest.MonkeyPatch
) -> None:
    streamlit_stub._allow_success = False
    times = iter(range(10))
    monkeypatch.setattr(webui.time, "time", lambda: next(times))

    ui = webui.WebUI()
    progress = ui.create_progress("<script>deploy</script>", total=2)
    subtask_id = progress.add_subtask("<b>subtask</b>", total=1)

    progress.update(advance=2)
    progress.update_subtask(subtask_id, advance=1)

    progress.complete()

    assert (
        progress._subtasks[subtask_id]["current"]
        == progress._subtasks[subtask_id]["total"]
    )
    assert streamlit_stub.write_messages == ["Completed: "]
    assert "<" not in streamlit_stub.write_messages[0]

    subtask_stub = streamlit_stub.subtasks[0]
    assert subtask_stub.success_calls == ["Completed: &lt;b&gt;subtask&lt;/b&gt;"]
    assert subtask_stub.progress_updates[-1] == 1.0

    status_block = streamlit_stub.status_blocks[0]
    markdown_messages = [
        text for action, text in status_block.calls if action == "markdown"
    ]
    assert markdown_messages
    assert all("<" not in text for text in markdown_messages)


def test_webui_layout_and_display_behaviors(
    streamlit_stub: _StubStreamlit, monkeypatch: pytest.MonkeyPatch
) -> None:
    ui = webui.WebUI()

    streamlit_stub.session_state.screen_width = 600
    mobile = ui.get_layout_config()
    assert mobile["columns"] == 1 and mobile["is_mobile"] is True

    streamlit_stub.session_state.screen_width = 900
    tablet = ui.get_layout_config()
    assert tablet["columns"] == 2 and tablet["is_mobile"] is False

    streamlit_stub.session_state.screen_width = 1280
    desktop = ui.get_layout_config()
    assert desktop["columns"] == 3

    answer = ui.ask_question("Pick an option", choices=("one", "two"), default="two")
    assert answer == "two"
    assert streamlit_stub.selectbox_calls[-1]["choices"] == ["one", "two"]

    freeform = ui.ask_question("Describe", default="value")
    assert freeform == "value"
    assert streamlit_stub.text_input_calls[-1]["value"] == "value"

    assert ui.confirm_choice("Proceed?", default=True) is True
    assert streamlit_stub.checkbox_calls[-1]["value"] is True

    ui.display_result("[bold]done[/bold]")
    assert streamlit_stub.markdown_messages[-1][0] == "**done**"

    streamlit_stub._allow_info = False
    ui.display_result("fallback info", highlight=True)
    assert streamlit_stub.write_messages[-1] == "fallback info"
    streamlit_stub._allow_info = True

    ui.display_result("Informative note", message_type="info")
    assert streamlit_stub.info_messages[-1] == "Informative note"

    ui.display_result("Great job", message_type="success")
    assert streamlit_stub.success_messages[-1] == "Great job"

    ui.display_result("Heads up", message_type="warning")
    assert streamlit_stub.warning_messages[-1] == "Heads up"

    ui.display_result("WARNING: caution in effect")
    assert streamlit_stub.warning_messages[-1] == "WARNING: caution in effect"

    ui.display_result("ERROR Connection error detected")
    assert streamlit_stub.error_messages[-1] == "ERROR Connection error detected"
    assert any(
        "Network Configuration" in msg or "Connection Troubleshooting" in msg
        for msg, _ in streamlit_stub.markdown_messages
    )

    ui.display_result("SUCCESS All steps completed successfully")
    assert (
        streamlit_stub.success_messages[-1]
        == "SUCCESS All steps completed successfully"
    )

    ui.display_result("# Primary Heading")
    ui.display_result("## Secondary Heading")
    ui.display_result("### Final Heading")
    assert streamlit_stub.headers[-1] == "Primary Heading"
    assert streamlit_stub.subheaders[-1] == "Secondary Heading"
    assert any(
        "**Final Heading**" in msg for msg, _ in streamlit_stub.markdown_messages
    )

    ui._render_traceback("Traceback details")
    assert streamlit_stub.code_blocks[-1]["text"] == "Traceback details"

    formatted = ui._format_error_message(ValueError("bad input"))
    assert formatted == "ValueError: bad input"

    sample_error_types = {
        "File not found: missing.txt": "file_not_found",
        "Permission denied for resource": "permission_denied",
        "Invalid parameter value": "invalid_parameter",
        "Invalid format provided": "invalid_format",
        "Missing key abc": "key_error",
        "Type error occurred": "type_error",
        "Configuration error detected": "config_error",
        "Connection error upstream": "connection_error",
        "API error 500": "api_error",
        "Validation error on payload": "validation_error",
        "Syntax error near token": "syntax_error",
        "Import error in module": "import_error",
        "No match": "",
    }
    for message, expected in sample_error_types.items():
        assert ui._get_error_type(message) == expected

    suggestions = ui._get_error_suggestions("invalid_parameter")
    assert "Check the command syntax" in suggestions[0]
    assert ui._get_error_suggestions("unknown_type") == []

    docs = ui._get_documentation_links("connection_error")
    assert "Connection Troubleshooting" in docs
    assert ui._get_documentation_links("unknown_type") == {}

    progress = ui.create_progress("Main Task", total=100)
    time_values = iter(range(1, 20))
    monkeypatch.setattr(webui.time, "time", lambda: next(time_values))

    progress.update(advance=10)
    progress.update(advance=15)
    progress.update(advance=25)
    progress.update(advance=25)
    progress.update(status="Custom status", advance=0)
    progress.update(advance=20)

    subtask_id = progress.add_subtask("<i>child</i>", total=5)
    progress.update_subtask(subtask_id, advance=2, description="<i>update</i>")
    progress.complete_subtask(subtask_id)
    progress.complete()

    assert streamlit_stub.success_messages[-1] == "Completed: Main Task"
    subtask_stub = streamlit_stub.subtasks[-1]
    assert subtask_stub.markdown_calls
    assert all(
        "&lt;i&gt;" in call or "&lt;" not in call
        for call in subtask_stub.markdown_calls
    )


def test_ui_progress_status_transitions_and_eta(
    streamlit_stub: _StubStreamlit, monkeypatch: pytest.MonkeyPatch
) -> None:
    times = iter([0, 30, 60, 120, 180, 240, 300, 360, 420])
    monkeypatch.setattr(webui.time, "time", lambda: next(times))

    ui = webui.WebUI()
    progress = ui.create_progress("Main Task", total=120)

    progress.update(advance=10)
    assert progress._status == "Starting..."

    progress.update(advance=20)
    assert progress._status == "Processing..."

    progress.update(advance=30)
    assert progress._status == "Halfway there..."

    progress.update(advance=30)
    assert progress._status == "Almost done..."

    progress.update(advance=29)
    assert progress._status == "Finalizing..."

    progress.update(description="<New Description>", status="<Done>", advance=0)
    assert progress._description == "&lt;New Description&gt;"
    assert progress._status == "&lt;Done&gt;"

    time_block = streamlit_stub.time_blocks[0]

    time_block.calls.clear()
    progress._update_times = [(0, 0), (10, 60), (20, 80), (25, 90)]
    progress._current = 95
    monkeypatch.setattr(webui.time, "time", lambda: 30)
    progress._update_display()
    assert time_block.calls[-1][0] == "info"
    assert "seconds" in time_block.calls[-1][1]

    time_block.calls.clear()
    progress._update_times = [
        (0, 0),
        (120, 10),
        (240, 20),
        (360, 30),
        (480, 40),
    ]
    progress._current = 50
    monkeypatch.setattr(webui.time, "time", lambda: 600)
    progress._update_display()
    assert "minutes" in time_block.calls[-1][1]

    time_block.calls.clear()
    progress._update_times = [
        (0, 0),
        (900, 2),
        (1800, 4),
        (2700, 5),
        (3600, 6),
    ]
    progress._current = 7
    progress._total = 50
    monkeypatch.setattr(webui.time, "time", lambda: 4500)
    progress._update_display()
    assert "hours" in time_block.calls[-1][1]

    time_block.calls.clear()
    progress._update_times = []
    progress._current = 0
    monkeypatch.setattr(webui.time, "time", lambda: 5000)
    progress._update_display()
    assert time_block.calls[-1] == ("empty", None)


def test_ensure_router_caches_instance(
    streamlit_stub: _StubStreamlit, monkeypatch: pytest.MonkeyPatch
) -> None:
    created: list[object] = []

    class _RouterStub:
        def __init__(self, owner: object, items: object) -> None:
            self.owner = owner
            self.items = items
            created.append(self)

        def run(self) -> None:  # pragma: no cover - exercised elsewhere
            return None

    monkeypatch.setattr(webui, "Router", _RouterStub)
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: ("one", "two"))

    ui = webui.WebUI()
    first = ui._ensure_router()
    second = ui._ensure_router()

    assert first is second
    assert len(created) == 1


def test_webui_run_configures_layout_and_router(
    streamlit_stub: _StubStreamlit, monkeypatch: pytest.MonkeyPatch
) -> None:
    routers: list[object] = []

    class _RouterStub:
        def __init__(self, owner: object, items: object) -> None:
            self.owner = owner
            self.items = tuple(items)
            self.run_calls = 0
            routers.append(self)

        def run(self) -> None:
            self.run_calls += 1

    streamlit_stub.session_state = _SessionState()
    monkeypatch.setattr(webui, "Router", _RouterStub)
    monkeypatch.setattr(
        webui.WebUI, "navigation_items", lambda self: ("dashboard", "settings")
    )

    ui = webui.WebUI()
    ui.run()

    assert streamlit_stub.set_page_config_calls[-1] == {
        "page_title": "DevSynth WebUI",
        "layout": "wide",
    }
    assert routers and routers[0].items == ("dashboard", "settings")
    assert routers[0].run_calls == 1
    assert streamlit_stub.components.calls
    assert "updateScreenWidth" in streamlit_stub.components.calls[0]["code"]
    assert streamlit_stub.sidebar.title_calls == ["DevSynth"]
    assert streamlit_stub.sidebar.markdown_calls


def test_webui_run_handles_streamlit_errors(
    streamlit_stub: _StubStreamlit, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: ())

    ui = webui.WebUI()
    streamlit_stub.raise_page_config = True
    ui.run()
    assert streamlit_stub.error_messages[-1] == "ERROR: set_page_config failure"
    assert ui._router is None

    streamlit_stub.raise_page_config = False
    streamlit_stub.raise_html_error = True
    streamlit_stub.components.calls.clear()
    ui.run()
    assert streamlit_stub.error_messages[-1] == "ERROR: html failure"
    assert ui._router is None
    assert streamlit_stub.components.calls == []
