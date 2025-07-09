import sys
from types import ModuleType
from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture
def stub_streamlit(monkeypatch):
    """Create a stub streamlit module for testing."""
    st = ModuleType('streamlit')


    class SS(dict):
        pass
    st.session_state = SS()
    st.button = MagicMock(return_value=False)
    st.spinner = MagicMock()
    st.spinner.return_value.__enter__ = MagicMock(return_value=None)
    st.spinner.return_value.__exit__ = MagicMock(return_value=None)
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    return st


@pytest.fixture
def mock_gather_requirements(monkeypatch):
    """Mock the gather_requirements function."""
    gather_mock = MagicMock()
    monkeypatch.setattr('devsynth.core.workflows.gather_requirements',
        gather_mock)
    return gather_mock


def test_gather_wizard_button_not_clicked_succeeds(stub_streamlit,
    mock_gather_requirements):
    """Test that gather_requirements is not called when button is not clicked.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    stub_streamlit.button.return_value = False
    WebUI()._gather_wizard()
    mock_gather_requirements.assert_not_called()
    stub_streamlit.button.assert_called_once()
    assert 'Start Requirements Plan Wizard' in stub_streamlit.button.call_args[
        1]['key']


def test_gather_wizard_button_clicked_succeeds(stub_streamlit,
    mock_gather_requirements):
    """Test that gather_requirements is called when button is clicked.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    stub_streamlit.button.return_value = True
    webui_instance = WebUI()
    webui_instance._gather_wizard()
    mock_gather_requirements.assert_called_once_with(webui_instance)
    stub_streamlit.spinner.assert_called_once()


def test_gather_wizard_import_error_fails(stub_streamlit, monkeypatch):
    """Test error handling when importing gather_requirements fails.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    stub_streamlit.button.return_value = True
    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if name == 'devsynth.core.workflows':
            raise ImportError('Test import error')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr('builtins.__import__', mock_import)
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    webui_instance._gather_wizard()
    webui_instance.display_result.assert_called_once()
    assert 'ERROR' in webui_instance.display_result.call_args[0][0]


def test_gather_wizard_runtime_error_raises_error(stub_streamlit,
    mock_gather_requirements):
    """Test error handling when gather_requirements raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    stub_streamlit.button.return_value = True
    mock_gather_requirements.side_effect = RuntimeError('Test runtime error')
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    webui_instance._gather_wizard()
    webui_instance.display_result.assert_called_once()
    assert 'ERROR' in webui_instance.display_result.call_args[0][0]
    assert 'Test runtime error' in webui_instance.display_result.call_args[0][0
        ]


def test_gather_wizard_with_patched_module_succeeds(stub_streamlit, monkeypatch
    ):
    """Test gather_wizard with a patched workflows module.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    stub_streamlit.button.return_value = True
    workflows_mock = ModuleType('devsynth.core.workflows')
    workflows_mock.gather_requirements = MagicMock()
    monkeypatch.setitem(sys.modules, 'devsynth.core.workflows', workflows_mock)
    webui_instance = WebUI()
    webui_instance._gather_wizard()
    workflows_mock.gather_requirements.assert_called_once_with(webui_instance)
