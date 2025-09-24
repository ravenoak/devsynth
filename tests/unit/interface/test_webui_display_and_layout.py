"""Unit tests covering WebUI layout selection and result rendering."""

from __future__ import annotations

import importlib
import sys
from typing import Any

import pytest

from tests.fixtures.fake_streamlit import FakeStreamlit

pytestmark = [pytest.mark.fast]


@pytest.fixture
def webui_module(monkeypatch):
    """Reload the WebUI module with a lightweight Streamlit substitute."""

    fake_streamlit = FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    return webui, fake_streamlit


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
