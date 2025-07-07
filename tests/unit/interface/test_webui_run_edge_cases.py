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
    
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st

def test_run_method_with_invalid_navigation(stub_streamlit):
    """Test the run method with an invalid navigation option."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create WebUI instance with mocked page methods and display_result
    webui_instance = WebUI()
    webui_instance.onboarding_page = MagicMock()
    webui_instance.requirements_page = MagicMock()
    webui_instance.display_result = MagicMock()
    
    # Set up an invalid navigation option
    stub_streamlit.sidebar.radio.return_value = "InvalidPage"
    
    # Run the WebUI
    webui_instance.run()
    
    # Verify that no page methods were called
    webui_instance.onboarding_page.assert_not_called()
    webui_instance.requirements_page.assert_not_called()
    
    # Verify that an error message was displayed
    webui_instance.display_result.assert_called_once()
    assert "ERROR" in webui_instance.display_result.call_args[0][0]
    assert "Invalid navigation option" in webui_instance.display_result.call_args[0][0]

def test_run_method_with_page_exception(stub_streamlit):
    """Test the run method when a page method raises an exception."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create WebUI instance with mocked page methods and display_result
    webui_instance = WebUI()
    webui_instance.onboarding_page = MagicMock(side_effect=RuntimeError("Test page error"))
    webui_instance.display_result = MagicMock()
    
    # Set up navigation to the page that will raise an exception
    stub_streamlit.sidebar.radio.return_value = "Onboarding"
    
    # Run the WebUI
    webui_instance.run()
    
    # Verify that the page method was called
    webui_instance.onboarding_page.assert_called_once()
    
    # Verify that an error message was displayed
    webui_instance.display_result.assert_called_once()
    assert "ERROR" in webui_instance.display_result.call_args[0][0]
    assert "Test page error" in webui_instance.display_result.call_args[0][0]

def test_run_method_with_streamlit_exception(stub_streamlit, monkeypatch):
    """Test the run method when streamlit raises an exception."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create WebUI instance with mocked display_result
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    
    # Mock set_page_config to raise an exception
    stub_streamlit.set_page_config.side_effect = RuntimeError("Test streamlit error")
    
    # Run the WebUI
    webui_instance.run()
    
    # Verify that an error message was displayed
    webui_instance.display_result.assert_called_once()
    assert "ERROR" in webui_instance.display_result.call_args[0][0]
    assert "Test streamlit error" in webui_instance.display_result.call_args[0][0]

def test_run_method_with_sidebar_exception(stub_streamlit):
    """Test the run method when sidebar raises an exception."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create WebUI instance with mocked display_result
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    
    # Mock sidebar.radio to raise an exception
    stub_streamlit.sidebar.radio.side_effect = RuntimeError("Test sidebar error")
    
    # Run the WebUI
    webui_instance.run()
    
    # Verify that an error message was displayed
    webui_instance.display_result.assert_called_once()
    assert "ERROR" in webui_instance.display_result.call_args[0][0]
    assert "Test sidebar error" in webui_instance.display_result.call_args[0][0]

def test_run_method_with_multiple_exceptions(stub_streamlit):
    """Test the run method when multiple exceptions occur."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create WebUI instance with mocked display_result
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    
    # Mock display_result to raise an exception
    webui_instance.display_result.side_effect = RuntimeError("Test display error")
    
    # Mock sidebar.radio to raise an exception
    stub_streamlit.sidebar.radio.side_effect = RuntimeError("Test sidebar error")
    
    # Run the WebUI and catch the exception
    with pytest.raises(RuntimeError) as excinfo:
        webui_instance.run()
    
    # Verify that the exception was raised
    assert "Test sidebar error" in str(excinfo.value)

def test_standalone_run_function(stub_streamlit, monkeypatch):
    """Test the standalone run function."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    
    # Mock WebUI class
    mock_webui = MagicMock()
    mock_webui_instance = MagicMock()
    mock_webui.return_value = mock_webui_instance
    monkeypatch.setattr("devsynth.interface.webui.WebUI", mock_webui)
    
    # Call the standalone run function
    webui.run()
    
    # Verify that WebUI was instantiated and run was called
    mock_webui.assert_called_once()
    mock_webui_instance.run.assert_called_once()

def test_run_webui_alias(stub_streamlit, monkeypatch):
    """Test the run_webui alias function."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    
    # Mock WebUI class
    mock_webui = MagicMock()
    mock_webui_instance = MagicMock()
    mock_webui.return_value = mock_webui_instance
    monkeypatch.setattr("devsynth.interface.webui.WebUI", mock_webui)
    
    # Call the run_webui alias function
    webui.run_webui()
    
    # Verify that WebUI was instantiated and run was called
    mock_webui.assert_called_once()
    mock_webui_instance.run.assert_called_once()

def test_main_block(stub_streamlit, monkeypatch):
    """Test the __main__ block."""
    import importlib
    
    # Mock the run function
    run_mock = MagicMock()
    
    # Create a mock module with the run function
    module = ModuleType("devsynth.interface.webui")
    module.run = run_mock
    module.__name__ = "__main__"
    
    # Execute the module's code
    exec("""
if __name__ == "__main__":
    run()
""", module.__dict__)
    
    # Verify that run was called
    run_mock.assert_called_once()