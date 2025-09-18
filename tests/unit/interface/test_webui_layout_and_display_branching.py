"""Unit tests covering layout and display logic for the WebUI facade."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import devsynth.interface.webui as webui_module

pytestmark = [pytest.mark.fast]


def _make_streamlit_stub(*, session_width: int | None = 1200) -> SimpleNamespace:
    """Create a ``SimpleNamespace`` mimicking the subset of Streamlit we exercise."""

    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
    session_state = (
        SimpleNamespace(screen_width=session_width)
        if session_width is not None
        else None
    )
    stub = SimpleNamespace(calls=calls, session_state=session_state)

    def record(name: str):
        def method(*args, **kwargs):
            calls.append((name, args, kwargs))
            return None

        return method

    for attribute in (
        "markdown",
        "write",
        "error",
        "warning",
        "success",
        "info",
        "header",
        "subheader",
    ):
        setattr(stub, attribute, record(attribute))

    return stub


def _install_streamlit_stub(
    monkeypatch: pytest.MonkeyPatch, stub: SimpleNamespace
) -> None:
    """Patch :mod:`devsynth.interface.webui` to use the provided Streamlit stub."""

    monkeypatch.setattr(webui_module, "_STREAMLIT", None)
    monkeypatch.setattr(webui_module, "_require_streamlit", lambda stub=stub: stub)


@pytest.mark.parametrize(
    ("screen_width", "expected"),
    [
        (
            640,
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
            820,
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
    ],
)
def test_get_layout_config_breakpoints(
    monkeypatch: pytest.MonkeyPatch, screen_width, expected
):
    """ReqID: N/A - ``WebUI.get_layout_config`` adapts layout by screen width."""

    stub = _make_streamlit_stub(session_width=screen_width)
    _install_streamlit_stub(monkeypatch, stub)

    ui = webui_module.WebUI()

    assert ui.get_layout_config() == expected


def test_display_result_rich_markup_uses_markdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: N/A - Rich markup renders via ``markdown`` with HTML spans."""

    stub = _make_streamlit_stub()
    _install_streamlit_stub(monkeypatch, stub)

    ui = webui_module.WebUI()
    ui.display_result("[bold]Alert[/bold] [red]Hot[/red]")

    assert stub.calls == [
        (
            "markdown",
            ('**Alert** <span style="color:red">Hot</span>',),
            {"unsafe_allow_html": True},
        )
    ]


def test_display_result_error_type_renders_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: N/A - ``message_type='error'`` surfaces suggestions and docs."""

    stub = _make_streamlit_stub()
    _install_streamlit_stub(monkeypatch, stub)

    ui = webui_module.WebUI()

    monkeypatch.setattr(
        webui_module.WebUI,
        "_get_error_type",
        lambda self, message: "deterministic_error",
    )
    monkeypatch.setattr(
        webui_module.WebUI,
        "_get_error_suggestions",
        lambda self, error_type: ["Check logs", "Restart service"],
    )
    monkeypatch.setattr(
        webui_module.WebUI,
        "_get_documentation_links",
        lambda self, error_type: {"Runbook": "https://example.invalid/runbook"},
    )

    ui.display_result("Failure detected", message_type="error")

    assert stub.calls == [
        ("error", ("Failure detected",), {}),
        ("markdown", ("**Suggestions:**",), {}),
        ("markdown", ("- Check logs",), {}),
        ("markdown", ("- Restart service",), {}),
        ("markdown", ("**Documentation:**",), {}),
        (
            "markdown",
            ("- [Runbook](https://example.invalid/runbook)",),
            {},
        ),
    ]


@pytest.mark.parametrize(
    ("message_type", "expected_method"),
    [
        ("warning", "warning"),
        ("success", "success"),
        ("info", "info"),
        ("unexpected", "write"),
    ],
)
def test_display_result_message_types(
    monkeypatch: pytest.MonkeyPatch, message_type, expected_method
) -> None:
    """ReqID: N/A - ``display_result`` delegates to Streamlit per type."""

    stub = _make_streamlit_stub()
    _install_streamlit_stub(monkeypatch, stub)

    ui = webui_module.WebUI()
    ui.display_result("Status update", message_type=message_type)

    assert stub.calls == [(expected_method, ("Status update",), {})]


def test_display_result_highlight_uses_info(monkeypatch: pytest.MonkeyPatch) -> None:
    """ReqID: N/A - Highlighting without type uses ``info`` output."""

    stub = _make_streamlit_stub()
    _install_streamlit_stub(monkeypatch, stub)

    ui = webui_module.WebUI()
    ui.display_result("Important highlight", highlight=True)

    assert stub.calls == [("info", ("Important highlight",), {})]


def test_display_result_defaults_to_write(monkeypatch: pytest.MonkeyPatch) -> None:
    """ReqID: N/A - Plain messages fall back to ``write`` output."""

    stub = _make_streamlit_stub()
    _install_streamlit_stub(monkeypatch, stub)

    ui = webui_module.WebUI()
    ui.display_result("Routine output")

    assert stub.calls == [("write", ("Routine output",), {})]


@pytest.mark.parametrize(
    ("message", "expected_calls"),
    [
        ("# Overview", [("header", ("Overview",), {})]),
        ("## Section", [("subheader", ("Section",), {})]),
        ("### Deep Dive", [("markdown", ("**Deep Dive**",), {})]),
    ],
)
def test_display_result_renders_headings(
    monkeypatch: pytest.MonkeyPatch, message: str, expected_calls
) -> None:
    """ReqID: N/A - Markdown headings map onto Streamlit helpers."""

    stub = _make_streamlit_stub()
    _install_streamlit_stub(monkeypatch, stub)

    ui = webui_module.WebUI()
    ui.display_result(message)

    assert stub.calls == expected_calls
