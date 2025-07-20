import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, call, mock_open
import pytest
from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Fixture to mock streamlit for testing."""
    st = _mock_streamlit()

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state['wizard_step'] = 0
    st.session_state.wizard_data = {
        "title": "",
        "description": "",
        "type": "functional",
        "priority": "medium",
        "constraints": "",
    }
    st.session_state['wizard_data'] = st.session_state.wizard_data
    st.button = MagicMock(return_value=False)
    st.text_area = MagicMock(return_value="desc")
    col1_mock = MagicMock(button=MagicMock(return_value=False))
    col2_mock = MagicMock(button=MagicMock(return_value=False))
    st.columns = MagicMock(return_value=(col1_mock, col2_mock))
    st._col1 = col1_mock
    st._col2 = col2_mock
    st.form = MagicMock()
    st.form.return_value.__enter__ = MagicMock(return_value=MagicMock())
    st.form.return_value.__exit__ = MagicMock(return_value=None)
    st.form_submit_button = MagicMock(return_value=False)
    st.expander = MagicMock()
    st.expander.return_value.__enter__ = MagicMock(return_value=MagicMock())
    st.expander.return_value.__exit__ = MagicMock(return_value=None)
    st.spinner = MagicMock()
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
    assert 'wizard_step' in mock_streamlit.session_state
    assert 'wizard_data' in mock_streamlit.session_state
    mock_streamlit.session_state['wizard_step'] = 0
    mock_streamlit.session_state.wizard_step = 0
    mock_streamlit._col2.button.return_value = True
    bridge._requirements_wizard()
    assert mock_streamlit.session_state.wizard_step == 1
    mock_streamlit._col2.button.return_value = False
    mock_streamlit.session_state['wizard_step'] = 4
    mock_streamlit.session_state.wizard_step = 4
    mock_streamlit.button.return_value = True
    m = mock_open()
    with patch("builtins.open", m):
        result = bridge._requirements_wizard()
    assert result is not None
    assert isinstance(result, dict)
