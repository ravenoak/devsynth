import sys
from unittest.mock import MagicMock

import pytest

from devsynth.interface.webui.routing import Router
from tests.fixtures.streamlit_mocks import make_streamlit_mock

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("force_webui_available"),
]


@pytest.fixture
def stub_streamlit(monkeypatch):
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


class StubUI:
    def __init__(self, st):
        self.streamlit = st
        self.messages: list[str] = []

    def display_result(self, message: str) -> None:
        self.messages.append(message)


def test_router_uses_session_state(stub_streamlit):
    """ReqID: FR-208 reuse stored navigation selection when available."""
    pages = {
        "Onboarding": MagicMock(),
        "Synthesis": MagicMock(),
    }
    stub_streamlit.session_state.nav = "Synthesis"
    stub_streamlit.sidebar.radio.return_value = "Synthesis"
    ui = StubUI(stub_streamlit)

    router = Router(ui, pages)
    router.run()

    stub_streamlit.sidebar.radio.assert_called_with(
        "Navigation", ["Onboarding", "Synthesis"], index=1
    )
    pages["Synthesis"].assert_called_once()
    assert stub_streamlit.session_state.nav == "Synthesis"


def test_router_resets_invalid_selection(stub_streamlit):
    """ReqID: FR-209 normalize invalid session state to defaults."""
    pages = {"Onboarding": MagicMock(), "Requirements": MagicMock()}
    stub_streamlit.session_state.nav = "Missing"
    stub_streamlit.sidebar.radio.return_value = "Onboarding"
    ui = StubUI(stub_streamlit)

    router = Router(ui, pages)
    router.run()

    stub_streamlit.sidebar.radio.assert_called_with(
        "Navigation", ["Onboarding", "Requirements"], index=0
    )
    pages["Onboarding"].assert_called_once()


def test_router_handles_sidebar_exception(stub_streamlit):
    """ReqID: FR-210 surface sidebar rendering failures."""
    pages = {"Onboarding": MagicMock()}
    stub_streamlit.sidebar.radio.side_effect = RuntimeError("boom")
    ui = StubUI(stub_streamlit)

    router = Router(ui, pages)
    router.run()

    assert ui.messages == ["ERROR: boom"]
    pages["Onboarding"].assert_not_called()


def test_router_surfaces_page_exception(stub_streamlit):
    """ReqID: FR-211 report page execution errors via the UI."""
    failing_page = MagicMock(side_effect=ValueError("kapow"))
    pages = {"Onboarding": failing_page}
    stub_streamlit.sidebar.radio.return_value = "Onboarding"
    ui = StubUI(stub_streamlit)

    router = Router(ui, pages)
    router.run()

    assert ui.messages == ["ERROR: kapow"]


def test_router_requires_pages(stub_streamlit):
    """ReqID: FR-212 require at least one page when instantiating the router."""
    ui = StubUI(stub_streamlit)
    with pytest.raises(ValueError):
        Router(ui, {})


def test_router_honors_explicit_default(stub_streamlit):
    """ReqID: FR-213 select the configured default page when no state exists."""

    pages = {
        "Onboarding": MagicMock(),
        "Requirements": MagicMock(),
    }
    stub_streamlit.session_state.pop("nav", None)
    stub_streamlit.sidebar.radio.return_value = "Requirements"
    ui = StubUI(stub_streamlit)

    router = Router(ui, pages, default="Requirements")
    router.run()

    stub_streamlit.sidebar.radio.assert_called_with(
        "Navigation", ["Onboarding", "Requirements"], index=1
    )
    pages["Requirements"].assert_called_once()


def test_router_reports_missing_page_handler(stub_streamlit):
    """ReqID: FR-214 surface invalid selections instead of crashing."""

    pages = {"Onboarding": MagicMock()}
    stub_streamlit.sidebar.radio.return_value = "Ghost"
    ui = StubUI(stub_streamlit)

    router = Router(ui, pages)
    router.run()

    assert ui.messages == ["ERROR: Invalid navigation option"]
    pages["Onboarding"].assert_not_called()
