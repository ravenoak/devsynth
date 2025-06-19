from types import ModuleType
from unittest.mock import MagicMock

import importlib
import sys

import pytest


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
def shared_ui(monkeypatch):
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
    st.text_input = MagicMock(return_value="text")
    st.text_area = MagicMock(return_value="desc")
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
    return {"st": st, "ui": webui.WebUI(), "cli": cli_module}


def test_cli_and_webui_use_same_command(shared_ui, monkeypatch):
    cli_module = shared_ui["cli"]

    # CLI invocation
    cli_module.init_cmd(
        path="demo", project_root="demo", language="python", bridge=shared_ui["ui"]
    )
    assert cli_module.init_cmd.called
    cli_module.init_cmd.reset_mock()

    # WebUI invocation
    shared_ui["st"].form_submit_button.return_value = True
    shared_ui["ui"].onboarding_page()
    assert cli_module.init_cmd.called
