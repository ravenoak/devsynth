import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock
from pathlib import Path

import pytest

from tests.unit.interface.test_streamlit_mocks import make_streamlit_mock


@pytest.fixture
def stub_streamlit(monkeypatch):
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


def _reload_webui():
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    return webui


def test_navigation_persists_wizard_state(monkeypatch, stub_streamlit):
    """Wizard step should persist when navigating between pages."""
    webui = _reload_webui()
    ui = webui.WebUI()

    # start on Requirements page and advance wizard
    stub_streamlit.sidebar.radio = MagicMock(return_value="Requirements")
    col1, col2 = stub_streamlit.columns.return_value
    col1.button = MagicMock(return_value=False)
    col2.button = MagicMock(return_value=True)
    ui._requirements_wizard()  # advance to step 1
    col2.button.return_value = False
    ui.run()  # store nav selection
    assert stub_streamlit.session_state.wizard_step == 1
    assert stub_streamlit.session_state.nav == "Requirements"

    # navigate away
    stub_streamlit.sidebar.radio = MagicMock(return_value="Onboarding")
    ui.run()
    assert stub_streamlit.session_state.nav == "Onboarding"
    # wizard step should remain unchanged
    assert stub_streamlit.session_state.wizard_step == 1

    # return to Requirements
    stub_streamlit.sidebar.radio = MagicMock(return_value="Requirements")
    ui.run()
    assert stub_streamlit.session_state.wizard_step == 1
    assert stub_streamlit.session_state.nav == "Requirements"


def test_analysis_page_invalid_path_shows_error(monkeypatch, stub_streamlit):
    """Invalid analysis path should trigger an error message."""
    webui = _reload_webui()
    ui = webui.WebUI()

    stub_streamlit.text_input.return_value = "bad_path"
    stub_streamlit.form_submit_button.return_value = True
    monkeypatch.setattr(Path, "exists", lambda *_a, **_k: False)

    cmd = MagicMock()
    monkeypatch.setattr(webui, "inspect_code_cmd", cmd)

    ui.analysis_page()

    # ensure the command was not executed and an error message shown
    cmd.assert_not_called()
    assert any(
        "not found" in call[0][0] for call in stub_streamlit.error.call_args_list
    )

