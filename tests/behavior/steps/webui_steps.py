import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

scenarios("../features/webui.feature")


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

    cli_stub = ModuleType("devsynth.application.cli")
    for name in [
        "init_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
        "doctor_cmd",
        "edrr_cycle_cmd",
        "align_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    analyze_stub = ModuleType("devsynth.application.cli.commands.inspect_code_cmd")
    analyze_stub.inspect_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.inspect_code_cmd", analyze_stub
    )

    doctor_stub = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    doctor_stub.doctor_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.doctor_cmd", doctor_stub
    )
    cli_stub.doctor_cmd = doctor_stub.doctor_cmd

    edrr_stub = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")
    edrr_stub.edrr_cycle_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.edrr_cycle_cmd", edrr_stub
    )
    cli_stub.edrr_cycle_cmd = edrr_stub.edrr_cycle_cmd

    align_stub = ModuleType("devsynth.application.cli.commands.align_cmd")
    align_stub.align_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.align_cmd", align_stub
    )
    cli_stub.align_cmd = align_stub.align_cmd

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    ctx = {
        "st": st,
        "cli": cli_stub,
        "webui": webui,
        "ui": webui.WebUI(),
    }
    return ctx


@given("the WebUI is initialized")
def given_webui_initialized(webui_context):
    return webui_context


@when(parsers.parse('I navigate to "{page}"'))
def navigate_to(page, webui_context):
    webui_context["st"].sidebar.radio.return_value = page
    webui_context["ui"].run()


@when("I submit the onboarding form")
def submit_onboarding(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Onboarding"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I update a configuration value")
def update_config(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Config"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@then(parsers.parse('the "{header}" header is shown'))
def check_header(header, webui_context):
    webui_context["st"].header.assert_any_call(header)


@then("the init command should be executed")
def check_init(webui_context):
    assert webui_context["cli"].init_cmd.called


@then("the config command should be executed")
def check_config(webui_context):
    assert webui_context["cli"].config_cmd.called
