from types import ModuleType
from unittest.mock import MagicMock
import sys
import importlib

import pytest
from pytest_bdd import given, when, then, scenarios

from devsynth.interface.webui import WebUI

scenarios("../features/general/requirements_wizard_navigation.feature")


class DummyForm:
    def __init__(self, submitted: bool = False):
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


@pytest.fixture
def wizard_context(monkeypatch):
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {}
    st.sidebar = ModuleType("sidebar")
    st.sidebar.radio = MagicMock(return_value="Requirements")
    st.sidebar.title = MagicMock()
    st.set_page_config = MagicMock()
    st.header = MagicMock()
    st.expander = lambda *_a, **_k: DummyForm(True)
    st.form = lambda *_a, **_k: DummyForm(True)
    st.form_submit_button = MagicMock(return_value=False)
    st.text_input = MagicMock(return_value="text")
    st.text_area = MagicMock(return_value="desc")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.button = MagicMock(side_effect=[False, True, False])
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

    ctx = {"st": st, "ui": webui.WebUI()}
    return ctx


@given("the WebUI is initialized")
def _init(wizard_context):
    return wizard_context


@when("I open the requirements wizard")
def open_wizard(wizard_context):
    wizard_context["st"].sidebar.radio.return_value = "Requirements"
    wizard_context["ui"].requirements_page()


@when("I click the wizard next button")
def click_next(wizard_context):
    col1 = MagicMock(button=lambda *a, **k: False)
    col2 = MagicMock(button=lambda *a, **k: True)
    wizard_context["st"].columns.return_value = (col1, col2)
    wizard_context["ui"]._requirements_wizard()


@when("I click the wizard back button")
def click_back(wizard_context):
    col1 = MagicMock(button=lambda *a, **k: True)
    col2 = MagicMock(button=lambda *a, **k: False)
    wizard_context["st"].columns.return_value = (col1, col2)
    wizard_context["ui"]._requirements_wizard()


@then("the wizard should show step 2")
def show_step_two(wizard_context):
    assert wizard_context["st"].session_state.wizard_step == 1


@then("the wizard should show step 1")
def show_step_one(wizard_context):
    assert wizard_context["st"].session_state.wizard_step == 0
