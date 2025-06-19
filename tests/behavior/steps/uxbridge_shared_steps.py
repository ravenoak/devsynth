"""Steps verifying shared UXBridge behavior between CLI and WebUI."""

from types import ModuleType
from unittest.mock import MagicMock
import importlib
import sys

import pytest
from pytest_bdd import given, when, then, scenarios

scenarios("../features/uxbridge_cli_webui.feature")


class DummyForm:
    """Simple context manager used to mock Streamlit forms."""

    def __init__(self, submitted: bool = True) -> None:
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


@pytest.fixture
def parity_context(monkeypatch):
    """Create a shared CLI and WebUI environment."""
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


@given("the CLI and WebUI share a UXBridge")
def shared_setup(parity_context):
    """Return the parity context."""
    return parity_context


@when("init is invoked from the CLI and WebUI")
def invoke_init(parity_context):
    """Invoke the init command via both interfaces."""
    cli_module = parity_context["cli"]
    ui = parity_context["ui"]
    st = parity_context["st"]
    cli_module.init_cmd(path="demo", project_root="demo", language="python", bridge=ui)
    st.form_submit_button.return_value = True
    ui.onboarding_page()


@then("both invocations pass identical arguments")
def check_calls(parity_context):
    """Ensure CLI calls from CLI and WebUI used the same parameters."""
    cli_module = parity_context["cli"]
    assert cli_module.init_cmd.call_count == 2
    args_api = cli_module.init_cmd.call_args_list[0].kwargs
    args_ui = cli_module.init_cmd.call_args_list[1].kwargs
    args_api.pop("bridge", None)
    args_ui.pop("bridge", None)
    assert args_api == args_ui
