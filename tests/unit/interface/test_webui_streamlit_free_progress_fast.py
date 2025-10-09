"""Streamlit-free WebUI regression coverage for routing, progress, and sanitization."""

from __future__ import annotations

"""Streamlit-free WebUI regression coverage for routing and progress telemetry."""

import importlib
import sys
from types import ModuleType
from typing import Iterator, Tuple
from unittest.mock import MagicMock

import pytest

from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def streamlit_free_webui(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Tuple[ModuleType, ModuleType, dict[str, MagicMock]]]:
    """Reload :mod:`devsynth.interface.webui` with a deterministic Streamlit stub."""

    st = _mock_streamlit()
    st.sidebar.radio = MagicMock(return_value="Summary")
    st.session_state.screen_width = 860
    st.session_state.screen_height = 600

    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui as webui

    importlib.reload(webui)

    navigation = {"Summary": MagicMock(name="summary_page")}

    monkeypatch.setattr(webui.PageRenderer, "navigation_items", lambda self: navigation)

    try:
        yield webui, st, navigation
    finally:
        sys.modules.pop("streamlit", None)
        importlib.reload(webui)


@pytest.fixture
def progress_webui(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Tuple[ModuleType, ModuleType, MagicMock, MagicMock, MagicMock]]:
    """Provide a reloaded WebUI module with deterministic progress containers."""

    st = _mock_streamlit()
    status_container = MagicMock(name="status_container")
    time_container = MagicMock(name="time_container")
    bar_container = MagicMock(name="bar_container")

    st.empty = MagicMock(side_effect=[status_container, time_container])
    st.progress = MagicMock(return_value=bar_container)

    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui as webui

    importlib.reload(webui)

    try:
        yield webui, st, status_container, time_container, bar_container
    finally:
        sys.modules.pop("streamlit", None)
        importlib.reload(webui)


@pytest.fixture
def sanitized_webui(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Tuple[ModuleType, ModuleType]]:
    """Yield a reloaded WebUI module for sanitization assertions."""

    st = _mock_streamlit()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui as webui

    importlib.reload(webui)

    try:
        yield webui, st
    finally:
        sys.modules.pop("streamlit", None)
        importlib.reload(webui)


@pytest.mark.fast
def test_webui_run_configures_dashboard_and_invokes_router(
    streamlit_free_webui: Tuple[ModuleType, ModuleType, dict[str, MagicMock]],
) -> None:
    """ReqID: WEBUI-DASH-TOGGLE-01 — Layout toggles wire routing without Streamlit."""

    webui, st, navigation = streamlit_free_webui
    ui = webui.WebUI()

    ui.run()

    assert isinstance(ui._router, webui.Router)
    assert ui._router.pages == navigation
    assert st.set_page_config.call_count == 1
    sidebar_css_calls = [call.args[0] for call in st.markdown.call_args_list]
    assert any(
        "sidebar-content" in payload and "30%" in payload
        for payload in sidebar_css_calls
    )
    st.sidebar.radio.assert_called_once_with("Navigation", list(navigation), index=0)


@pytest.mark.fast
def test_progress_updates_emit_telemetry_and_sanitize_checkpoints(
    progress_webui: Tuple[ModuleType, ModuleType, MagicMock, MagicMock, MagicMock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: WEBUI-PROGRESS-TRACE-02 — Progress checkpoints sanitize and log telemetry."""

    webui, st, status_container, time_container, bar_container = progress_webui

    sanitized_inputs: list[str] = []

    def capture_sanitize(text: str) -> str:
        sanitized_inputs.append(text)
        return f"safe::{text}"

    logger_spy = MagicMock()

    monkeypatch.setattr(webui, "sanitize_output", capture_sanitize)
    monkeypatch.setattr(webui, "logger", logger_spy)

    ui = webui.WebUI()
    progress = ui.create_progress("Download <file>", total=4)

    step_id = progress.add_subtask("Subtask <A>", total=4, status="In <progress>")
    progress.update(advance=1, description="Chunk <1>")
    progress.update_subtask(step_id, advance=2, description="Stage <2>")
    progress.complete_subtask(step_id)
    progress.complete()

    assert sanitized_inputs == [
        "Download <file>",
        "Subtask <A>",
        "In <progress>",
        "Chunk <1>",
        "Stage <2>",
    ]

    status_payloads = [
        call.args[0] for call in status_container.markdown.call_args_list
    ]
    assert any(
        payload.startswith("**safe::Download <file>") for payload in status_payloads
    )
    bar_updates = [call.args[0] for call in bar_container.progress.call_args_list]
    assert bar_updates[0] == 0.0
    assert pytest.approx(bar_updates[-1]) == 1.0
    assert logger_spy.debug.call_count >= 3


@pytest.mark.fast
def test_display_result_sanitizes_message_before_render(
    sanitized_webui: Tuple[ModuleType, ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: WEBUI-SAN-03 — Bridge output sanitization precedes rendering hooks."""

    webui, st = sanitized_webui

    sanitized_inputs: list[str] = []

    def capture_sanitize(message: str) -> str:
        sanitized_inputs.append(message)
        return f"clean::{message}"

    monkeypatch.setattr(webui, "sanitize_output", capture_sanitize)

    ui = webui.WebUI()
    ui.display_result("<script>alert('x')</script>", message_type="info")

    assert sanitized_inputs == ["<script>alert('x')</script>"]
    st.info.assert_called_once_with("clean::<script>alert('x')</script>")
