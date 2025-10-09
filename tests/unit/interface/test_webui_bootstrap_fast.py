from __future__ import annotations

import pytest

from devsynth.interface import webui
from tests.helpers.dummies import DummyStreamlit


@pytest.mark.fast
def test_webui_run_registers_router_and_hydrates_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_streamlit = DummyStreamlit()
    recorded: dict[str, object] = {}

    class DummyRouter:
        def __init__(
            self, ui, pages
        ) -> None:  # noqa: ANN001 - interface dictated by Router
            recorded["ui"] = ui
            recorded["pages"] = dict(pages)

        def run(self) -> None:
            recorded["ran"] = True

    monkeypatch.setattr(webui, "st", dummy_streamlit)
    monkeypatch.setattr(webui, "Router", DummyRouter)

    ui = webui.WebUI()
    ui.run()

    assert recorded["ui"] is ui
    assert recorded["pages"] == ui.navigation_items()
    assert recorded.get("ran") is True
    assert dummy_streamlit.set_page_config_calls
    assert dummy_streamlit.session_state["screen_width"] == 1200
    assert dummy_streamlit.session_state["screen_height"] == 800


@pytest.mark.fast
def test_webui_command_dispatch_invokes_cli_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_streamlit = DummyStreamlit()
    monkeypatch.setattr(webui, "st", dummy_streamlit)

    ui = webui.WebUI()
    executed: dict[str, object] = {}

    def sample_cmd(*, subject: str) -> str:
        executed["subject"] = subject
        return "ok"

    monkeypatch.setattr(webui, "sample_cmd", sample_cmd)

    command = ui._cli("sample_cmd")
    assert command is sample_cmd

    result = ui._handle_command_errors(command, "Execution failed", subject="demo")

    assert result == "ok"
    assert executed == {"subject": "demo"}


@pytest.mark.fast
def test_webui_command_dispatch_reports_value_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_streamlit = DummyStreamlit()
    monkeypatch.setattr(webui, "st", dummy_streamlit)

    ui = webui.WebUI()
    captured: list[tuple[str, str | None]] = []

    def capture(
        message: str, *, highlight: bool = False, message_type: str | None = None
    ) -> None:
        captured.append((message, message_type))

    monkeypatch.setattr(ui, "display_result", capture)

    def failing_command() -> None:
        raise ValueError("bad input")

    result = ui._handle_command_errors(failing_command, "Failed to execute")

    assert result is None
    assert any(
        "Invalid value" in message
        for message, category in captured
        if category == "error"
    )
    assert any("Please check your input" in message for message, _ in captured)
