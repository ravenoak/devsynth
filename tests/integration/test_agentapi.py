"""Integration tests for the AgentAPI wrapper."""
from types import ModuleType
from unittest.mock import MagicMock
import sys
import importlib

from devsynth.interface.ux_bridge import UXBridge


def _setup(monkeypatch):
    cli_stub = ModuleType("devsynth.application.cli")
    for name in [
        "init_cmd",
        "spec_cmd",
        "inspect_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "config_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    analyze_stub = ModuleType("devsynth.application.cli.commands.analyze_code_cmd")
    analyze_stub.analyze_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.analyze_code_cmd",
        analyze_stub,
    )

    st = ModuleType("streamlit")
    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {}
    st.sidebar = ModuleType("sidebar")
    st.sidebar.radio = MagicMock(return_value="Onboarding")
    st.sidebar.title = MagicMock()
    st.set_page_config = MagicMock()
    st.header = MagicMock()
    st.expander = lambda *_a, **_k: DummyForm(True)
    st.form = lambda *_a, **_k: DummyForm(True)
    st.form_submit_button = MagicMock(return_value=True)
    st.text_input = MagicMock(return_value="text")
    st.text_area = MagicMock(return_value="desc")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.button = MagicMock(return_value=False)
    st.spinner = DummyForm
    st.divider = MagicMock()
    st.columns = MagicMock(return_value=(MagicMock(button=lambda *a, **k: False), MagicMock(button=lambda *a, **k: False)))
    st.progress = MagicMock()
    st.write = MagicMock()
    st.markdown = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui as webui
    importlib.reload(webui)

    return cli_stub, webui


class DummyForm:
    def __init__(self, submitted: bool = True):
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


def test_init_matches_webui(monkeypatch):
    cli_stub, webui = _setup(monkeypatch)
    bridge = MagicMock(spec=UXBridge)
    from devsynth.interface.agentapi import AgentAPI
    api = AgentAPI(bridge)
    api.init(path="text", project_root="text", language="text", goals="text")

    ui = webui.WebUI()
    ui.onboarding_page()

    assert cli_stub.init_cmd.call_count == 2
    args_api = cli_stub.init_cmd.call_args_list[0].kwargs
    args_ui = cli_stub.init_cmd.call_args_list[1].kwargs
    args_api.pop("bridge", None)
    args_ui.pop("bridge", None)
    assert args_api == args_ui


def test_spec_matches_webui(monkeypatch):
    cli_stub, webui = _setup(monkeypatch)
    bridge = MagicMock(spec=UXBridge)
    from devsynth.interface.agentapi import AgentAPI
    api = AgentAPI(bridge)
    api.spec("req.md")

    webui.st.sidebar.radio.return_value = "Requirements"
    webui.st.form_submit_button.side_effect = [True, False]
    webui.WebUI().run()

    assert cli_stub.spec_cmd.call_count == 2
    args_api = cli_stub.spec_cmd.call_args_list[0].kwargs
    args_ui = cli_stub.spec_cmd.call_args_list[1].kwargs
    args_api.pop("bridge", None)
    args_ui.pop("bridge", None)
    assert args_api == args_ui


def test_config_matches_webui(monkeypatch):
    cli_stub, webui = _setup(monkeypatch)
    bridge = MagicMock(spec=UXBridge)
    from devsynth.interface.agentapi import AgentAPI
    api = AgentAPI(bridge)
    api.config(key="model", value="gpt-4")

    webui.st.sidebar.radio.return_value = "Config"
    webui.st.form_submit_button.return_value = True
    webui.st.text_input.side_effect = ["model", "gpt-4"]
    webui.WebUI().run()

    assert cli_stub.config_cmd.call_count == 2
    args_api = cli_stub.config_cmd.call_args_list[0].kwargs
    args_ui = cli_stub.config_cmd.call_args_list[1].kwargs
    args_api.pop("bridge", None)
    args_ui.pop("bridge", None)
    assert args_api == args_ui
