from types import ModuleType
from unittest.mock import MagicMock
import importlib
import sys

import pytest

from devsynth.interface.cli import CLIUXBridge


class DummyForm:
    def __init__(self, submitted: bool = True) -> None:
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


@pytest.fixture
def parity_env(monkeypatch):
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())

    from devsynth.application import cli as cli_module
    monkeypatch.setattr(cli_module, "init_cmd", MagicMock())

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
    st.text_input = MagicMock(side_effect=["demo", "demo", "python", ""])
    st.text_area = MagicMock(return_value="demo goals")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.button = MagicMock(return_value=True)
    st.spinner = DummyForm
    st.divider = MagicMock()
    st.columns = MagicMock(
        return_value=(
            MagicMock(button=lambda *a, **k: False),
            MagicMock(button=lambda *a, **k: False),
        )
    )
    st.progress = MagicMock()
    st.write = MagicMock()
    st.markdown = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui as webui
    importlib.reload(webui)
    return cli_module, webui.WebUI()


def test_init_invocations_match(parity_env):
    cli_module, webui_bridge = parity_env
    cli_bridge = CLIUXBridge()

    cli_module.init_cmd(path="demo", project_root="demo", language="python", goals=None, bridge=cli_bridge)
    args_cli = cli_module.init_cmd.call_args_list[-1].kwargs
    cli_module.init_cmd.reset_mock()

    webui_bridge.onboarding_page()
    args_web = cli_module.init_cmd.call_args_list[-1].kwargs

    args_cli.pop("bridge", None)
    args_web.pop("bridge", None)
    assert args_cli == args_web
