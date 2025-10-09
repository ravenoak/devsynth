"""Unit tests covering WebUI layout selection and result rendering."""

from __future__ import annotations

import importlib
import os
import sys
from typing import Any

import pytest

from tests.fixtures.fake_streamlit import FakeStreamlit

pytestmark = [pytest.mark.fast]

COVERAGE_MODE = os.getenv("DEVSYNTH_WEBUI_COVERAGE") == "1"


@pytest.fixture
def webui_module(monkeypatch):
    """Reload the WebUI module with a lightweight Streamlit substitute."""

    fake_streamlit = FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    import devsynth.interface.webui as webui

    module = importlib.reload(webui)
    monkeypatch.setattr(module, "_STREAMLIT", fake_streamlit, raising=False)
    monkeypatch.setattr(module, "st", fake_streamlit, raising=False)
    return module, fake_streamlit


def test_require_streamlit_lazy_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lazy ``st`` proxy loads Streamlit only when accessed."""

    fake_streamlit = FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    import devsynth.interface.webui as webui

    module = webui if COVERAGE_MODE else importlib.reload(webui)
    monkeypatch.setattr(module, "_STREAMLIT", None, raising=False)
    monkeypatch.setattr(module, "st", module._LazyStreamlit(), raising=False)

    loaded = module._require_streamlit()
    assert loaded is fake_streamlit

    module.st.write("lazy access")
    assert fake_streamlit.write_calls[-1] == "lazy access"


@pytest.mark.parametrize(
    "width, expected",
    [
        (
            500,
            {
                "columns": 1,
                "sidebar_width": "100%",
                "content_width": "100%",
                "font_size": "small",
                "padding": "0.5rem",
                "is_mobile": True,
            },
        ),
        (
            800,
            {
                "columns": 2,
                "sidebar_width": "30%",
                "content_width": "70%",
                "font_size": "medium",
                "padding": "1rem",
                "is_mobile": False,
            },
        ),
        (
            1200,
            {
                "columns": 3,
                "sidebar_width": "20%",
                "content_width": "80%",
                "font_size": "medium",
                "padding": "1.5rem",
                "is_mobile": False,
            },
        ),
        (
            None,
            {
                "columns": 3,
                "sidebar_width": "20%",
                "content_width": "80%",
                "font_size": "medium",
                "padding": "1.5rem",
                "is_mobile": False,
            },
        ),
    ],
)
def test_get_layout_config_breakpoints(
    webui_module: tuple[Any, FakeStreamlit], width: int | None, expected: dict[str, Any]
) -> None:
    """``get_layout_config`` adapts layout metadata to screen width."""

    webui, fake_streamlit = webui_module
    if width is not None:
        fake_streamlit.session_state.screen_width = width
    else:
        fake_streamlit.session_state.pop("screen_width", None)

    layout = webui.WebUI().get_layout_config()
    assert layout == expected


def test_display_result_renders_markup_and_sanitizes(monkeypatch, webui_module):
    """Markup content is converted to Markdown with sanitized payloads."""

    webui, fake_streamlit = webui_module
    sanitized_inputs: list[str] = []

    def record_and_escape(text: str) -> str:
        sanitized_inputs.append(text)
        return text.replace("<danger>", "&lt;danger&gt;")

    monkeypatch.setattr(webui, "sanitize_output", record_and_escape)

    ui = webui.WebUI()
    ui.display_result("[bold]Alert[/bold] with [red]danger[/red] <danger>")

    assert sanitized_inputs == ["[bold]Alert[/bold] with [red]danger[/red] <danger>"]
    assert (
        fake_streamlit.markdown_calls
    ), "Expected markdown rendering for markup content"

    content, kwargs = fake_streamlit.markdown_calls[0]
    assert "**Alert**" in content
    assert '<span style="color:red">danger</span>' in content
    assert "&lt;danger&gt;" in content
    assert kwargs.get("unsafe_allow_html") is True
    assert not fake_streamlit.write_calls


def test_display_result_highlight_uses_info(monkeypatch, webui_module):
    """Highlighted messages prefer ``st.info`` and still sanitize text."""

    webui, fake_streamlit = webui_module
    sanitized_inputs: list[str] = []

    def sanitizer(text: str) -> str:
        sanitized_inputs.append(text)
        return f"sanitized::{text}"

    monkeypatch.setattr(webui, "sanitize_output", sanitizer)

    ui = webui.WebUI()
    ui.display_result("Important <notice>", highlight=True)

    assert sanitized_inputs == ["Important <notice>"]
    assert fake_streamlit.info_calls == ["sanitized::Important <notice>"]
    assert not fake_streamlit.write_calls


def test_display_result_routes_message_types_and_plain_write(
    monkeypatch: pytest.MonkeyPatch, webui_module
) -> None:
    """Message types map to their Streamlit channels while sanitizing content."""

    webui, fake_streamlit = webui_module
    sanitized_inputs: list[str] = []

    def recorder(text: str) -> str:
        sanitized_inputs.append(text)
        return text

    monkeypatch.setattr(webui, "sanitize_output", recorder)

    ui = webui.WebUI()
    ui.display_result("warn", message_type="warning")
    ui.display_result("ok", message_type="success")
    ui.display_result("info", message_type="info")
    ui.display_result("note", message_type="note")

    assert sanitized_inputs == ["warn", "ok", "info", "note"]
    assert fake_streamlit.warning_calls[-1] == "warn"
    assert fake_streamlit.success_calls[-1] == "ok"
    assert fake_streamlit.info_calls[-1] == "info"
    assert fake_streamlit.write_calls[-1] == "note"


def test_display_result_error_suggestions_and_docs(monkeypatch, webui_module):
    """Error messages surface contextual suggestions and documentation links."""

    webui, fake_streamlit = webui_module
    sanitized_inputs: list[str] = []

    def sanitizer(text: str) -> str:
        sanitized_inputs.append(text)
        return text

    monkeypatch.setattr(webui, "sanitize_output", sanitizer)

    ui = webui.WebUI()
    message = "ERROR: File not found: config.yaml"
    ui.display_result(message, message_type="error")

    assert sanitized_inputs == [message]
    assert fake_streamlit.error_calls == [message]

    markdown_texts = [content for content, _kwargs in fake_streamlit.markdown_calls]
    assert "**Suggestions:**" in markdown_texts
    assert any("Check that the file path is correct" in text for text in markdown_texts)
    assert "**Documentation:**" in markdown_texts
    assert any("File Handling Guide" in text for text in markdown_texts)


def test_display_result_error_prefix_without_message_type(
    monkeypatch: pytest.MonkeyPatch, webui_module
) -> None:
    """Error-prefixed messages trigger helper lookups even without ``message_type``."""

    webui, fake_streamlit = webui_module
    captured: list[str] = []

    def passthrough(text: str) -> str:
        captured.append(text)
        return text

    monkeypatch.setattr(webui, "sanitize_output", passthrough)

    ui = webui.WebUI()
    message = "ERROR: Permission denied during write"
    ui.display_result(message)

    assert captured == [message]
    assert fake_streamlit.error_calls[-1] == message
    markdown_texts = [content for content, _ in fake_streamlit.markdown_calls]
    assert any("**Suggestions:**" in text for text in markdown_texts)
    assert any("Permission Issues" in text for text in markdown_texts)


def test_display_result_heading_routes_to_header(monkeypatch, webui_module):
    """Markdown headings are routed to the appropriate Streamlit heading APIs."""

    webui, fake_streamlit = webui_module
    sanitized_inputs: list[str] = []

    def sanitizer(text: str) -> str:
        sanitized_inputs.append(text)
        return text

    monkeypatch.setattr(webui, "sanitize_output", sanitizer)

    ui = webui.WebUI()
    ui.display_result("# Welcome to DevSynth")

    assert sanitized_inputs == ["# Welcome to DevSynth"]
    assert fake_streamlit.header_calls == ["Welcome to DevSynth"]
    assert not fake_streamlit.markdown_calls


def test_display_result_additional_headings(monkeypatch, webui_module) -> None:
    """Heading level 2 and deeper render via subheader and markdown fallback."""

    webui, fake_streamlit = webui_module
    monkeypatch.setattr(webui, "sanitize_output", lambda text: text)

    ui = webui.WebUI()
    ui.display_result("## Secondary Title")
    ui.display_result("### Deep Heading")

    assert fake_streamlit.subheader_calls == ["Secondary Title"]
    bold_sections = [
        content
        for content, _ in fake_streamlit.markdown_calls
        if content.startswith("**")
    ]
    assert bold_sections == ["**Deep Heading**"]


@pytest.mark.parametrize(
    "message, expected",
    [
        ("File not found: missing.yaml", "file_not_found"),
        ("Permission denied when opening", "permission_denied"),
        ("Invalid parameter --foo", "invalid_parameter"),
        ("Invalid format provided", "invalid_format"),
        ("Missing key 'api'", "key_error"),
        ("Type error while casting", "type_error"),
        ("Configuration error detected", "config_error"),
        ("Connection error occurred", "connection_error"),
        ("API error status", "api_error"),
        ("Validation error raised", "validation_error"),
        ("Syntax error unexpected token", "syntax_error"),
        ("Import error for module", "import_error"),
        ("Unrelated message", ""),
    ],
)
def test_get_error_type_mappings(
    webui_module: tuple[Any, FakeStreamlit], message: str, expected: str
) -> None:
    """Error helper categorises messages into documented types."""

    webui, _ = webui_module
    ui = webui.WebUI()
    assert ui._get_error_type(message) == expected


def test_error_helper_defaults(webui_module: tuple[Any, FakeStreamlit]) -> None:
    """Unknown error types produce empty guidance collections."""

    webui, _ = webui_module
    ui = webui.WebUI()
    assert ui._get_error_suggestions("mystery") == []
    assert ui._get_documentation_links("mystery") == {}


def test_render_traceback_uses_expander(
    webui_module: tuple[Any, FakeStreamlit],
) -> None:
    """Traceback rendering writes to an expander block with Python highlighting."""

    webui, fake_streamlit = webui_module
    ui = webui.WebUI()
    ui._render_traceback("Traceback contents")

    assert fake_streamlit.expanders, "Expected expander to be created"
    assert fake_streamlit.code_calls == [("Traceback contents", {"language": "python"})]


def test_format_error_message(webui_module: tuple[Any, FakeStreamlit]) -> None:
    """Exceptions render with type name prefix and message."""

    webui, _ = webui_module
    ui = webui.WebUI()
    assert ui._format_error_message(ValueError("bad")) == "ValueError: bad"


def test_ensure_router_caches_instance(
    monkeypatch: pytest.MonkeyPatch, webui_module
) -> None:
    """Router creation happens once and is memoised for future calls."""

    webui, _ = webui_module
    created: list[tuple[object, tuple]] = []

    class DummyRouter:
        def __init__(self, ui, items):
            created.append((ui, tuple(items)))

        def run(self) -> None:  # pragma: no cover - not used here
            pass

    monkeypatch.setattr(webui, "Router", DummyRouter)
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: ("home", "docs"))

    ui = webui.WebUI()
    router1 = ui._ensure_router()
    router2 = ui._ensure_router()

    assert router1 is router2
    assert created and created[0][1] == ("home", "docs")


def test_run_configures_streamlit_and_router(
    monkeypatch: pytest.MonkeyPatch, webui_module
) -> None:
    """Happy path run wires router, injects assets, and sets defaults."""

    webui, fake_streamlit = webui_module
    runs: list[str] = []

    class DummyRouter:
        def __init__(self, ui, items):
            self.ui = ui
            self.items = tuple(items)

        def run(self) -> None:
            runs.append("ran")

    monkeypatch.setattr(webui, "Router", DummyRouter)
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: ("Onboarding",))

    ui = webui.WebUI()
    ui.run()

    assert fake_streamlit.set_page_config_calls == [
        {"page_title": "DevSynth WebUI", "layout": "wide"}
    ]
    assert fake_streamlit.components_html_calls
    assert fake_streamlit.session_state["screen_width"] == 1200
    assert fake_streamlit.sidebar_title_calls == ["DevSynth"]
    assert runs == ["ran"]


def test_run_handles_page_config_error(
    monkeypatch: pytest.MonkeyPatch, webui_module
) -> None:
    """Page configuration failures route through ``display_result`` and exit early."""

    webui, fake_streamlit = webui_module
    fake_streamlit.set_page_config_exception = RuntimeError("boom")
    recorded: list[str] = []

    monkeypatch.setattr(
        webui.WebUI, "display_result", lambda self, message: recorded.append(message)
    )

    webui.WebUI().run()

    assert recorded == ["ERROR: boom"]
    assert fake_streamlit.components_html_calls == []


def test_run_handles_components_error(
    monkeypatch: pytest.MonkeyPatch, webui_module
) -> None:
    """Component injection errors surface via ``display_result``."""

    webui, fake_streamlit = webui_module

    def raising_html(*_args, **_kwargs):
        raise RuntimeError("html")

    fake_streamlit.components.v1.html = raising_html
    recorded: list[str] = []

    monkeypatch.setattr(
        webui.WebUI, "display_result", lambda self, message: recorded.append(message)
    )

    webui.WebUI().run()

    assert recorded == ["ERROR: html"]


def test_ui_progress_updates_emit_eta(
    monkeypatch: pytest.MonkeyPatch, webui_module: tuple[Any, FakeStreamlit]
) -> None:
    """Progress updates emit ETA information and track markdown/progress calls."""

    webui, fake_streamlit = webui_module

    timeline = iter([0.0, 5.0, 10.0, 12.0])

    def deterministic_time() -> float:
        try:
            return next(timeline)
        except StopIteration:  # pragma: no cover - defensive
            return 12.0

    monkeypatch.setattr(webui.time, "time", deterministic_time)
    monkeypatch.setattr(webui, "sanitize_output", lambda value: f"safe::{value}")

    progress = webui.WebUI().create_progress("Task", total=100)

    status_placeholder, time_placeholder = fake_streamlit.placeholders[:2]
    status_placeholder.markdown_calls.clear()
    time_placeholder.info_calls.clear()
    time_placeholder.empty_calls = 0
    bar = fake_streamlit.progress_bars[0]
    bar.progress_calls.clear()

    progress.update(advance=20, description="Phase 1")
    progress.update(advance=30)

    assert progress._status == "Halfway there..."
    assert status_placeholder.markdown_calls[-1] == "**safe::Phase 1** - 50%"
    assert bar.progress_calls[-1] == 0.5
    assert any("ETA:" in call for call in time_placeholder.info_calls)


def test_ui_progress_subtask_flow(
    monkeypatch: pytest.MonkeyPatch, webui_module
) -> None:
    """Subtask helpers update containers and mark completion."""

    webui, fake_streamlit = webui_module
    monkeypatch.setattr(webui, "sanitize_output", lambda value: f"safe::{value}")

    progress = webui.WebUI().create_progress("Parent", total=10)

    subtask_id = progress.add_subtask("Child", total=4)
    subtask_entry = progress._subtask_containers[subtask_id]
    container = subtask_entry["container"]
    bar = subtask_entry["bar"]

    assert container.markdown_calls[-1].endswith("0%")
    assert bar.progress_calls[-1] == 0.0

    progress.update_subtask(subtask_id, advance=2, description="Step")
    assert (
        container.markdown_calls[-1] == "&nbsp;&nbsp;&nbsp;&nbsp;**safe::Step** - 50%"
    )
    assert bar.progress_calls[-1] == 0.5

    progress.complete_subtask(subtask_id)
    assert container.success_calls[-1] == "Completed: safe::Step"

    progress.complete()
    assert fake_streamlit.success_calls[-1] == "Completed: safe::Parent"


def test_webui_ensure_router_caches_instance(monkeypatch, webui_module) -> None:
    """``_ensure_router`` only instantiates the router a single time."""

    webui, _ = webui_module
    router_instances: list[object] = []

    class DummyRouter:
        def __init__(self, bridge: object, nav: dict[str, object]):
            self.bridge = bridge
            self.nav = nav
            router_instances.append(self)

        def run(self) -> None:  # pragma: no cover - not invoked here
            raise AssertionError("run should not execute in caching test")

    monkeypatch.setattr(webui, "Router", DummyRouter)
    monkeypatch.setattr(
        webui.WebUI,
        "navigation_items",
        lambda self: {"Home": lambda: None},
        raising=False,
    )

    ui = webui.WebUI()
    first = ui._ensure_router()
    second = ui._ensure_router()

    assert first is second
    assert router_instances == [first]
    assert list(first.nav.keys()) == ["Home"]


def test_webui_run_configures_layout_and_router(monkeypatch, webui_module) -> None:
    """``run`` wires Streamlit primitives and executes the router."""

    webui, fake_streamlit = webui_module
    run_events: list[tuple[str, object]] = []

    class DummyRouter:
        def __init__(self, bridge: object, nav: dict[str, object]):
            run_events.append(("init", bridge, nav))

        def run(self) -> None:
            run_events.append(("run", None, None))

    monkeypatch.setattr(webui, "Router", DummyRouter)
    monkeypatch.setattr(
        webui.WebUI,
        "navigation_items",
        lambda self: {"Home": lambda: None},
        raising=False,
    )

    ui = webui.WebUI()
    ui.run()

    assert fake_streamlit.set_page_config_calls == [
        {"page_title": "DevSynth WebUI", "layout": "wide"}
    ]

    assert fake_streamlit.components_html_calls, "Expected responsive HTML injection"

    css_markup, css_kwargs = fake_streamlit.markdown_calls[0]
    assert ".main .block-container" in css_markup
    assert css_kwargs.get("unsafe_allow_html") is True

    assert fake_streamlit.sidebar_title_calls[-1] == "DevSynth"
    sidebar_html, sidebar_kwargs = fake_streamlit.sidebar_markdown_calls[-1]
    assert "Intelligent Software Development" in sidebar_html
    assert sidebar_kwargs.get("unsafe_allow_html") is True

    assert fake_streamlit.session_state.screen_width == 1200
    assert fake_streamlit.session_state.screen_height == 800

    assert run_events[0][0] == "init"
    assert run_events[0][1] is ui
    assert list(run_events[0][2].keys()) == ["Home"]
    assert run_events[-1][0] == "run"


def test_webui_run_handles_page_config_error(monkeypatch, webui_module) -> None:
    """Failure during page configuration reports the error and aborts."""

    webui, fake_streamlit = webui_module
    fake_streamlit.set_page_config_exception = RuntimeError("boom")

    def unexpected_router(*_args, **_kwargs):  # pragma: no cover - defensive
        raise AssertionError("Router should not be instantiated on failure")

    monkeypatch.setattr(webui, "Router", unexpected_router)

    ui = webui.WebUI()
    ui.run()

    assert fake_streamlit.error_calls[-1].startswith("ERROR: boom")
    assert fake_streamlit.sidebar_title_calls == []


def test_webui_run_handles_component_error(monkeypatch, webui_module) -> None:
    """Errors from the responsive HTML injection are surfaced and stop execution."""

    webui, fake_streamlit = webui_module

    def raising_html(*_args, **_kwargs) -> None:
        raise RuntimeError("html failure")

    fake_streamlit.components.v1.html = raising_html

    def unexpected_router(*_args, **_kwargs):  # pragma: no cover - defensive
        raise AssertionError("Router should not be instantiated when HTML fails")

    monkeypatch.setattr(webui, "Router", unexpected_router)

    ui = webui.WebUI()
    ui.run()

    assert fake_streamlit.error_calls[-1].startswith("ERROR: html failure")
    assert not fake_streamlit.sidebar_title_calls
