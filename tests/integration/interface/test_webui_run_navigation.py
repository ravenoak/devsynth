"""Medium-scope tests covering the WebUI ``run`` bootstrap and navigation hooks."""

from __future__ import annotations

import importlib
import sys
from typing import Any

import pytest

from tests.fixtures.fake_streamlit import FakeStreamlit

pytestmark = [pytest.mark.medium]


@pytest.fixture
def webui_module(monkeypatch):
    """Reload the WebUI module with a controlled Streamlit substitute."""

    fake_streamlit = FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    return webui, fake_streamlit


def test_run_injects_assets_and_resets_navigation(monkeypatch, webui_module):
    """``run`` injects resize hooks, CSS, and stabilises navigation defaults."""

    webui, fake_streamlit = webui_module
    created: dict[str, Any] = {}

    class StubRouter:
        def __init__(self, ui, pages, *_, **__):
            self.ui = ui
            self.pages = dict(pages)
            self.default = next(iter(self.pages))
            self.run_called = False
            self.selected: str | None = None
            created["instance"] = self

        def run(self) -> None:
            self.run_called = True
            st = self.ui.streamlit
            session_state = getattr(st, "session_state", None)
            stored = None
            if session_state is not None:
                stored = getattr(session_state, "nav", None)
                if hasattr(session_state, "get"):
                    stored = session_state.get("nav", stored)
                if stored not in self.pages:
                    session_state.nav = self.default
                    if hasattr(session_state, "__setitem__"):
                        session_state["nav"] = self.default
                self.selected = getattr(session_state, "nav", self.default)
            else:
                self.selected = self.default

    monkeypatch.setattr(webui, "Router", StubRouter)

    fake_streamlit.session_state.nav = "Missing"
    fake_streamlit.session_state["nav"] = "Missing"

    ui = webui.WebUI()
    ui.run()

    router = created["instance"]
    assert router.run_called
    assert router.selected == "Onboarding"

    assert fake_streamlit.session_state.screen_width == 1200
    assert fake_streamlit.session_state.screen_height == 800
    assert fake_streamlit.session_state["nav"] == "Onboarding"

    assert fake_streamlit.components_html_calls
    script, kwargs = fake_streamlit.components_html_calls[0]
    assert "updateScreenWidth" in script
    assert kwargs.get("height") == 0

    css_calls = [
        entry for entry in fake_streamlit.markdown_calls if "<style>" in entry[0]
    ]
    assert css_calls
    assert css_calls[0][1].get("unsafe_allow_html") is True

    assert fake_streamlit.sidebar_title_calls == ["DevSynth"]
    assert any(
        "devsynth-secondary" in text
        for text, _ in fake_streamlit.sidebar_markdown_calls
    )


def test_run_handles_page_config_errors(monkeypatch, webui_module):
    """Configuration failures surface through ``display_result`` without bootstrapping UI assets."""

    webui, fake_streamlit = webui_module
    fake_streamlit.set_page_config_exception = RuntimeError("blocked")

    ui = webui.WebUI()
    recorded: list[tuple[str, dict[str, Any]]] = []

    def capture(message: str, **kwargs: Any) -> None:
        recorded.append((message, kwargs))

    monkeypatch.setattr(ui, "display_result", capture)

    ui.run()

    assert recorded == [("ERROR: blocked", {})]
    assert fake_streamlit.set_page_config_calls == [
        {"page_title": "DevSynth WebUI", "layout": "wide"}
    ]
    assert not fake_streamlit.components_html_calls
    assert not fake_streamlit.markdown_calls
