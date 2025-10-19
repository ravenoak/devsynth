"""Fast checks for the WebUI run flow."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from devsynth.interface import webui as webui_module

WebUI = webui_module.WebUI


@pytest.fixture
def streamlit_router_stub(monkeypatch: pytest.MonkeyPatch):
    """Provide a stubbed Streamlit module and Router replacement."""

    from devsynth.interface import webui as webui_module

    previous_streamlit = sys.modules.get("streamlit")
    # Import Router from the webui package submodule
    from devsynth.interface.webui import Router

    previous_router = Router
    previous_cached_streamlit = webui_module._STREAMLIT

    st = ModuleType("streamlit")
    st.set_page_config = MagicMock()
    st.markdown = MagicMock()

    components = ModuleType("components")
    v1 = ModuleType("components.v1")
    v1.html = MagicMock()
    components.v1 = v1
    st.components = components

    class SessionState(dict):
        def __getattr__(self, name: str):  # pragma: no cover - defensive
            try:
                return self[name]
            except KeyError as exc:  # pragma: no cover - defensive
                raise AttributeError(name) from exc

        def __setattr__(self, name: str, value):
            self[name] = value

    st.session_state = SessionState()

    st.sidebar = SimpleNamespace(
        title=MagicMock(),
        markdown=MagicMock(),
    )

    monkeypatch.setitem(sys.modules, "streamlit", st)

    class RouterStub:
        instances: list[RouterStub] = []

        def __init__(self, *args, **kwargs) -> None:
            self.init_args = args
            self.init_kwargs = kwargs
            self.run_calls = 0
            RouterStub.instances.append(self)

        def run(self) -> None:
            self.run_calls += 1

    RouterStub.instances = []

    monkeypatch.setattr(webui_module, "Router", RouterStub)
    webui_module._STREAMLIT = None

    try:
        yield st, RouterStub
    finally:
        webui_module.Router = previous_router
        webui_module._STREAMLIT = previous_cached_streamlit

        if previous_streamlit is not None:
            sys.modules["streamlit"] = previous_streamlit
        else:
            sys.modules.pop("streamlit", None)


@pytest.mark.fast
def test_webui_run_injects_resize_script_and_configures_layout(streamlit_router_stub):
    st, router_stub = streamlit_router_stub

    webui = WebUI()

    html_mock = st.components.v1.html
    session_state = st.session_state

    webui.run()

    html_mock.assert_called_once()
    script_arg = html_mock.call_args.args[0]
    assert "updateScreenWidth" in script_arg
    assert html_mock.call_args.kwargs == {"height": 0}

    assert session_state["screen_width"] == 1200
    assert session_state["screen_height"] == 800

    st.markdown.assert_called_once()
    css_arg = st.markdown.call_args.args[0]
    assert css_arg.startswith("\n        <style>")
    assert st.markdown.call_args.kwargs["unsafe_allow_html"] is True

    st.sidebar.title.assert_called_once_with("DevSynth")
    st.sidebar.markdown.assert_called_once()
    sidebar_html = st.sidebar.markdown.call_args.args[0]
    assert "Intelligent Software Development" in sidebar_html
    assert st.sidebar.markdown.call_args.kwargs["unsafe_allow_html"] is True

    st.set_page_config.assert_called_once_with(
        page_title="DevSynth WebUI", layout="wide"
    )

    assert len(router_stub.instances) == 1
    router_instance = router_stub.instances[0]
    assert router_instance.init_args[0] is webui
    assert router_instance.run_calls == 1

    html_mock.reset_mock()
    html_mock.side_effect = RuntimeError("boom")

    webui_with_error = WebUI()
    webui_with_error.display_result = MagicMock()

    webui_with_error.run()

    html_mock.assert_called_once()
    webui_with_error.display_result.assert_called_once()
    error_message = webui_with_error.display_result.call_args.args[0]
    assert "ERROR" in error_message
    assert "boom" in error_message

    assert len(router_stub.instances) == 1

    html_mock.side_effect = None
