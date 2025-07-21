import sys
from types import ModuleType
from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture
def stub_streamlit(monkeypatch):
    """Create a stub streamlit module for testing."""
    st = ModuleType("streamlit")
    st.set_page_config = MagicMock()
    st.sidebar = MagicMock()
    st.sidebar.title = MagicMock()
    st.sidebar.radio = MagicMock(return_value="Onboarding")

    class SessionState(dict):
        """Dictionary with attribute access to mimic ``st.session_state``."""

        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError as exc:  # pragma: no cover - defensive
                raise AttributeError(name) from exc

        def __setattr__(self, name, value):
            self[name] = value

    st.session_state = SessionState()

    components = ModuleType("components")
    v1 = ModuleType("components.v1")
    v1.html = MagicMock()
    components.v1 = v1
    st.components = components

    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


def test_run_method_with_invalid_navigation_is_valid(stub_streamlit):
    """Test the run method with an invalid navigation option.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    webui_instance = WebUI()
    webui_instance.onboarding_page = MagicMock()
    webui_instance.requirements_page = MagicMock()
    webui_instance.display_result = MagicMock()
    stub_streamlit.sidebar.radio.return_value = 'InvalidPage'
    webui_instance.run()
    webui_instance.onboarding_page.assert_not_called()
    webui_instance.requirements_page.assert_not_called()
    webui_instance.display_result.assert_called_once()
    assert 'ERROR' in webui_instance.display_result.call_args[0][0]
    assert 'Invalid navigation option' in webui_instance.display_result.call_args[
        0][0]


def test_run_method_with_page_exception_raises_error(stub_streamlit):
    """Test the run method when a page method raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    webui_instance = WebUI()
    webui_instance.onboarding_page = MagicMock(side_effect=RuntimeError(
        'Test page error'))
    webui_instance.display_result = MagicMock()
    stub_streamlit.sidebar.radio.return_value = 'Onboarding'
    webui_instance.run()
    webui_instance.onboarding_page.assert_called_once()
    webui_instance.display_result.assert_called_once()
    assert 'ERROR' in webui_instance.display_result.call_args[0][0]
    assert 'Test page error' in webui_instance.display_result.call_args[0][0]


def test_run_method_with_streamlit_exception_raises_error(stub_streamlit,
    monkeypatch):
    """Test the run method when streamlit raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    stub_streamlit.set_page_config.side_effect = RuntimeError(
        'Test streamlit error')
    webui_instance.run()
    webui_instance.display_result.assert_called_once()
    assert 'ERROR' in webui_instance.display_result.call_args[0][0]
    assert 'Test streamlit error' in webui_instance.display_result.call_args[0
        ][0]


def test_run_method_with_sidebar_exception_raises_error(stub_streamlit):
    """Test the run method when sidebar raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    stub_streamlit.sidebar.radio.side_effect = RuntimeError(
        'Test sidebar error')
    webui_instance.run()
    webui_instance.display_result.assert_called_once()
    assert 'ERROR' in webui_instance.display_result.call_args[0][0]
    assert 'Test sidebar error' in webui_instance.display_result.call_args[0][0
        ]


def test_run_method_with_multiple_exceptions_raises_error(stub_streamlit):
    """Test the run method when multiple exceptions occur.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    webui_instance.display_result.side_effect = RuntimeError(
        'Test display error')
    stub_streamlit.sidebar.radio.side_effect = RuntimeError(
        'Test sidebar error')
    with pytest.raises(RuntimeError) as excinfo:
        webui_instance.run()
    assert 'Test sidebar error' in str(excinfo.value)


def test_standalone_run_function_succeeds(stub_streamlit, monkeypatch):
    """Test the standalone run function.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    mock_webui = MagicMock()
    mock_webui_instance = MagicMock()
    mock_webui.return_value = mock_webui_instance
    monkeypatch.setattr('devsynth.interface.webui.WebUI', mock_webui)
    webui.run()
    mock_webui.assert_called_once()
    mock_webui_instance.run.assert_called_once()


def test_run_webui_alias_succeeds(stub_streamlit, monkeypatch):
    """Test the run_webui alias function.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    mock_webui = MagicMock()
    mock_webui_instance = MagicMock()
    mock_webui.return_value = mock_webui_instance
    monkeypatch.setattr('devsynth.interface.webui.WebUI', mock_webui)
    webui.run_webui()
    mock_webui.assert_called_once()
    mock_webui_instance.run.assert_called_once()


def test_main_block_succeeds(stub_streamlit, monkeypatch):
    """Test the __main__ block.

ReqID: N/A"""
    import importlib
    run_mock = MagicMock()
    module = ModuleType('devsynth.interface.webui')
    module.run = run_mock
    module.__name__ = '__main__'
    exec('\nif __name__ == "__main__":\n    run()\n', module.__dict__)
    run_mock.assert_called_once()
