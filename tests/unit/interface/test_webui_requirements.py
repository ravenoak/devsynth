import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, call
import pytest
from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Fixture to mock streamlit for testing."""
    st = _mock_streamlit()
    st.session_state = {}
    st.session_state['wizard_step'] = 0
    st.session_state['wizard_data'] = {}
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    return st


@pytest.fixture
def mock_spec_cmd(monkeypatch):
    """Fixture to mock spec_cmd for testing."""
    spec_cmd = MagicMock()
    cli_module = ModuleType('devsynth.application.cli')
    cli_module.spec_cmd = spec_cmd
    monkeypatch.setitem(sys.modules, 'devsynth.application.cli', cli_module)
    return spec_cmd


@pytest.fixture
def mock_requirement_types(monkeypatch):
    """Fixture to mock RequirementType and RequirementPriority enums."""
    req_module = ModuleType('devsynth.domain.models.requirement')


    class MockRequirementType:
        FUNCTIONAL = 'functional'
        NON_FUNCTIONAL = 'non_functional'
        CONSTRAINT = 'constraint'


    class MockRequirementPriority:
        MUST_HAVE = 'must_have'
        SHOULD_HAVE = 'should_have'
        COULD_HAVE = 'could_have'
        WONT_HAVE = 'wont_have'
    req_module.RequirementType = MockRequirementType
    req_module.RequirementPriority = MockRequirementPriority
    monkeypatch.setitem(sys.modules, 'devsynth.domain.models.requirement',
        req_module)


def test_requirements_page_succeeds(mock_streamlit, mock_spec_cmd,
    mock_requirement_types):
    """Test the requirements_page method.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    bridge = WebUI()
    bridge.requirements_page()
    mock_streamlit.header.assert_called_with('Requirements Gathering')
    assert mock_streamlit.form.called
    mock_streamlit.form_submit_button.return_value = True
    bridge.requirements_page()
    assert mock_spec_cmd.called


def test_requirements_wizard_succeeds(mock_streamlit, mock_requirement_types):
    """Test the _requirements_wizard method.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    bridge = WebUI()
    bridge._requirements_wizard()
    assert mock_streamlit.form.called
    assert 'wizard_step' in mock_streamlit.session_state
    assert 'wizard_data' in mock_streamlit.session_state
    mock_streamlit.form_submit_button.return_value = True
    mock_streamlit.session_state['wizard_step'] = 0
    bridge._requirements_wizard()
    assert mock_streamlit.session_state['wizard_step'] == 1
    mock_streamlit.session_state['wizard_step'] = 3
    result = bridge._requirements_wizard()
    assert result is not None
    assert isinstance(result, dict)
