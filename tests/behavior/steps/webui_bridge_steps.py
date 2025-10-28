"""BDD steps validating Streamlit bridge message routing."""

from __future__ import annotations

import html
from types import ModuleType
from typing import Any
from collections.abc import Callable

import pytest
from pytest_bdd import given, parsers, then, when

import tests.fixtures.webui_test_utils as webui_test_utils_module
from devsynth.interface import webui_bridge
from tests.fixtures.fake_streamlit import FakeStreamlit
from tests.fixtures.webui_bridge_stub import install_streamlit_stub
from tests.fixtures.webui_test_utils import webui_context  # noqa: F401

pytestmark = [pytest.mark.gui, pytest.mark.medium]

webui_test_utils_module.ModuleType = ModuleType


@pytest.fixture
def streamlit_bridge_stub(monkeypatch: pytest.MonkeyPatch):
    """Provide a shared Streamlit stub after stubbing heavy WebUI modules."""

    _load_webui(monkeypatch)
    stub = FakeStreamlit()
    install_streamlit_stub(stub, monkeypatch)

    from devsynth.interface import webui_bridge as bridge_module

    assert bridge_module._require_streamlit() is stub
    return stub


@pytest.fixture
def mock_streamlit(streamlit_bridge_stub):
    """Reuse the shared Streamlit stub from the bridge fixtures."""

    # Ensure the stub is clean for each scenario run.
    streamlit_bridge_stub.session_state.clear()
    streamlit_bridge_stub.sidebar_radio_selection = None
    streamlit_bridge_stub.markdown_calls.clear()
    streamlit_bridge_stub.write_calls.clear()
    streamlit_bridge_stub.error_calls.clear()
    streamlit_bridge_stub.info_calls.clear()
    streamlit_bridge_stub.success_calls.clear()
    streamlit_bridge_stub.warning_calls.clear()
    streamlit_bridge_stub.header_calls.clear()
    streamlit_bridge_stub.subheader_calls.clear()
    streamlit_bridge_stub.components_html_calls.clear()
    streamlit_bridge_stub.sidebar_title_calls.clear()
    streamlit_bridge_stub.sidebar_markdown_calls.clear()
    streamlit_bridge_stub.sidebar_radio_calls.clear()
    streamlit_bridge_stub.set_page_config_calls.clear()
    return streamlit_bridge_stub


def _load_webui(monkeypatch: pytest.MonkeyPatch):
    """Load the WebUI class while stubbing heavy rendering dependencies."""

    import sys
    from types import ModuleType

    rendering_key = "devsynth.interface.webui.rendering"
    sys.modules.pop(rendering_key, None)
    rendering_module = ModuleType(rendering_key)

    class _StubPageRenderer:
        def __init__(self) -> None:
            super().__init__()

        def navigation_items(self) -> dict[str, Callable[[], None]]:
            return {}

    rendering_module.PageRenderer = _StubPageRenderer
    rendering_module.__all__ = ["PageRenderer"]
    monkeypatch.setitem(sys.modules, rendering_key, rendering_module)

    commands_key = "devsynth.interface.webui.commands"
    sys.modules.pop(commands_key, None)
    commands_module = ModuleType(commands_key)
    commands_module.__all__ = ["noop_command"]
    commands_module.noop_command = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, commands_key, commands_module)

    from devsynth.interface.webui import WebUI

    return WebUI


def _run_router(
    context: dict[str, Any],
    pages: dict[str, Callable[[], None]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Execute the WebUI router with a specific page mapping."""

    ui = context["ui"]
    monkeypatch.setattr(ui, "navigation_items", lambda: pages, raising=False)
    ui._router = None  # type: ignore[attr-defined]
    ui.run()


def _to_plain_text(value: Any) -> str:
    """Return a plain string representation of ``value``."""

    if hasattr(value, "plain"):
        return str(getattr(value, "plain"))
    return str(value)


@given("the WebUI bridge is initialized")
def initialize_bridge(
    webui_context: dict[str, Any],
    streamlit_bridge_stub,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """Instantiate WebUI and WebUIBridge with the shared Streamlit stub."""

    context = webui_context
    context["st"] = streamlit_bridge_stub
    streamlit_bridge_stub.session_state.clear()
    streamlit_bridge_stub.session_state.nav = None
    context["bridge"] = webui_bridge.WebUIBridge()
    WebUI = _load_webui(monkeypatch)
    install_streamlit_stub(streamlit_bridge_stub, monkeypatch)
    context["ui"] = WebUI()
    context["pages"] = {}
    monkeypatch.setattr(context["ui"], "_router", None, raising=False)
    return context


@given(parsers.parse('the stubbed sidebar selects "{page}"'))
def seed_sidebar(streamlit_bridge_stub, page: str) -> None:
    """Prime the sidebar selection for deterministic routing."""

    streamlit_bridge_stub.sidebar_radio_selection = page
    streamlit_bridge_stub.session_state.nav = page


@when(parsers.parse('the "{page}" page renders successfully'))
def render_success_page(
    page: str,
    webui_context: dict[str, Any],
    streamlit_bridge_stub,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Route to a page that emits a sanitized success message via the bridge."""

    raw_message = "Completed <script>alert('ok')</script> run"
    expected = html.escape(raw_message)
    webui_context["expected_success"] = expected

    bridge: webui_bridge.WebUIBridge = webui_context["bridge"]

    def _page() -> None:
        bridge.display_result(raw_message, message_type="success")

    pages = {page: _page}
    webui_context["pages"] = pages
    _run_router(webui_context, pages, monkeypatch)
    # Ensure Streamlit captured the selection for the next assertions.
    streamlit_bridge_stub.session_state.nav = page


@when(parsers.parse('the "{page}" page raises an error'))
def render_error_page(
    page: str,
    webui_context: dict[str, Any],
    streamlit_bridge_stub,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Route to a page that raises an error handled by the router."""

    error_detail = "<danger> failure"
    webui_context["expected_error"] = f"ERROR: {html.escape(error_detail)}"

    def _page() -> None:
        raise RuntimeError(error_detail)

    pages = {page: _page}
    webui_context["pages"] = pages
    _run_router(webui_context, pages, monkeypatch)
    streamlit_bridge_stub.session_state.nav = page


@then("the Streamlit stub records a sanitized success message")
def assert_success(streamlit_bridge_stub, webui_context: dict[str, Any]) -> None:
    """Verify the stub captured a sanitized success payload."""

    recorded = streamlit_bridge_stub.success_calls
    assert recorded, "Expected at least one success call recorded by the stub"
    message = _to_plain_text(recorded[-1])
    expected = webui_context.get("expected_success")
    assert expected is not None, "Expected success message was not seeded"
    assert "script" not in message
    assert "alert" not in message
    assert "<" not in message, message

    bridge: webui_bridge.WebUIBridge = webui_context["bridge"]
    assert bridge.messages, "Bridge should record formatted messages"
    bridge_message = _to_plain_text(bridge.messages[-1])
    assert "script" not in bridge_message
    assert "alert" not in bridge_message
    assert "<" not in bridge_message, bridge_message


@then("the Streamlit stub records a sanitized error message")
def assert_error(streamlit_bridge_stub, webui_context: dict[str, Any]) -> None:
    """Verify the stub captured a sanitized error payload."""

    recorded = streamlit_bridge_stub.error_calls
    assert recorded, "Expected at least one error call recorded by the stub"
    message = _to_plain_text(recorded[-1])
    expected = webui_context.get("expected_error")
    assert expected is not None, "Expected error message was not seeded"
    assert message == expected
    assert "<" not in message
