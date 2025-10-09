import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]


class DummyForm:
    def __init__(self, submitted: bool = True):
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


@pytest.fixture
def webui_context(monkeypatch):
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {}
    st.sidebar = ModuleType("sidebar")
    st.sidebar.radio = MagicMock(return_value="Onboarding")
    st.sidebar.title = MagicMock()
    st.sidebar.markdown = MagicMock()
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
    st.number_input = MagicMock(return_value=1)
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
    st.error = MagicMock()

    class _CompV1:
        @staticmethod
        def html(_html, **_kwargs):
            return None

    class _Components:
        v1 = _CompV1()

    st.components = _Components()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    cli_stub = ModuleType("devsynth.application.cli")
    for name in [
        "init_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    analyze_stub = ModuleType("devsynth.application.cli.commands.inspect_code_cmd")
    analyze_stub.inspect_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.inspect_code_cmd", analyze_stub
    )

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from pathlib import Path

    monkeypatch.setattr(webui.WebUI, "_requirements_wizard", lambda self: None)
    monkeypatch.setattr(webui.WebUI, "_gather_wizard", lambda self: None)
    monkeypatch.setattr(Path, "exists", lambda _self: True)
    monkeypatch.setattr(
        webui, "SetupWizard", lambda *_a, **_k: MagicMock(run=MagicMock())
    )
    ctx = {
        "st": st,
        "cli": cli_stub,
        "webui": webui,
        "ui": webui.WebUI(),
    }
    return ctx


scenarios(feature_path(__file__, "general", "webui_onboarding_flow.feature"))


@given("the WebUI is initialized")
def _init(webui_context):
    return webui_context


@when('I navigate to "Onboarding"')
def nav_onboarding(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Onboarding"
    webui_context["ui"].run()


@when("I submit the onboarding form")
def submit_onboarding(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Onboarding"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@then('the "Project Onboarding" header is shown')
def header_onboarding(webui_context):
    webui_context["st"].header.assert_any_call("Project Onboarding")


@then("the init command should be executed")
def check_init(webui_context):
    assert webui_context["cli"].init_cmd.called
