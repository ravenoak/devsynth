import sys
from unittest.mock import MagicMock, patch
import pytest
from pathlib import Path
from tests.unit.interface.streamlit_mocks import make_streamlit_mock


@pytest.fixture
def stub_streamlit(monkeypatch):
    """Provide a shared Streamlit mock for WebUI tests."""
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    return st


def test_onboarding_page_init_cmd_error_raises_error(stub_streamlit,
    monkeypatch):
    """Test error handling when init_cmd raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    # Mock init_cmd to accept any arguments and raise an error
    init_cmd_mock = MagicMock(side_effect=RuntimeError('Test init error'))
    monkeypatch.setattr('devsynth.application.cli.init_cmd', init_cmd_mock)
    # Set button to True to trigger the form submission
    stub_streamlit.form_submit_button.return_value = True
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    webui_instance.onboarding_page()
    # Verify that display_result was called with the error message
    assert any('ERROR' in call[0][0] and 'Test init error' in call[0][0] 
               for call in webui_instance.display_result.call_args_list)
    # Verify that init_cmd was called with the expected arguments
    init_cmd_mock.assert_called_once()


def test_onboarding_page_setup_wizard_error_raises_error(stub_streamlit,
    monkeypatch):
    """Test error handling when SetupWizard raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    # Mock init_cmd to avoid errors
    init_cmd_mock = MagicMock()
    monkeypatch.setattr('devsynth.application.cli.init_cmd', init_cmd_mock)
    # Mock SetupWizard to raise an error when run is called
    setup_wizard_mock = MagicMock()
    setup_wizard_mock.return_value.run.side_effect = RuntimeError(
        'Test setup error')
    monkeypatch.setattr('devsynth.application.cli.setup_wizard.SetupWizard',
        setup_wizard_mock)
    # Set button to True to trigger the guided setup
    stub_streamlit.button.return_value = True
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    webui_instance.onboarding_page()
    # Verify that display_result was called with the error message
    assert any('ERROR' in call[0][0] and 'Test setup error' in call[0][0] 
               for call in webui_instance.display_result.call_args_list)
    # Verify that SetupWizard was created and run was called
    setup_wizard_mock.assert_called_once()
    setup_wizard_mock.return_value.run.assert_called_once()


def test_requirements_page_spec_cmd_error_raises_error(stub_streamlit,
    monkeypatch):
    """Test error handling when spec_cmd raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    # Mock Path.exists to return True so the file validation passes
    monkeypatch.setattr('pathlib.Path.exists', lambda self: True)
    # Mock spec_cmd to raise an error
    spec_cmd_mock = MagicMock(side_effect=RuntimeError('Test spec error'))
    monkeypatch.setattr('devsynth.application.cli.spec_cmd', spec_cmd_mock)
    # Set form_submit_button to True to trigger the form submission
    stub_streamlit.form_submit_button.return_value = True
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    webui_instance.requirements_page()
    # Verify that display_result was called with the error message
    assert any('ERROR' in call[0][0] and 'Test spec error' in call[0][0] 
               for call in webui_instance.display_result.call_args_list)
    # Verify that spec_cmd was called
    spec_cmd_mock.assert_called_once()


def test_requirements_page_inspect_cmd_error_raises_error(stub_streamlit,
    monkeypatch):
    """Test error handling when inspect_cmd raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    # Mock Path.exists to return True so the file validation passes
    monkeypatch.setattr('pathlib.Path.exists', lambda self: True)
    # Mock spec_cmd to avoid errors
    spec_cmd_mock = MagicMock()
    monkeypatch.setattr('devsynth.application.cli.spec_cmd', spec_cmd_mock)
    # Mock inspect_cmd to raise an error
    inspect_cmd_mock = MagicMock(side_effect=RuntimeError('Test inspect error'))
    monkeypatch.setattr('devsynth.application.cli.inspect_cmd', inspect_cmd_mock)
    # Set form_submit_button to True to trigger the form submission
    # First call is for spec_cmd, second call is for inspect_cmd
    stub_streamlit.form_submit_button.side_effect = [False, True]
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    webui_instance.requirements_page()
    # Verify that display_result was called with the error message
    assert any('ERROR' in call[0][0] and 'Test inspect error' in call[0][0] 
               for call in webui_instance.display_result.call_args_list)
    # Verify that inspect_cmd was called
    inspect_cmd_mock.assert_called_once()


def test_requirements_page_file_not_found_raises_error(stub_streamlit,
    monkeypatch):
    """Test error handling when file is not found.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    # Mock Path.exists to return False for the first check and True for the second
    # This will trigger the file not found error in the first form
    exists_mock = MagicMock(side_effect=[False, True])
    monkeypatch.setattr('pathlib.Path.exists', exists_mock)
    # Mock spec_cmd and inspect_cmd to avoid errors
    spec_cmd_mock = MagicMock()
    monkeypatch.setattr('devsynth.application.cli.spec_cmd', spec_cmd_mock)
    inspect_cmd_mock = MagicMock()
    monkeypatch.setattr('devsynth.application.cli.inspect_cmd', inspect_cmd_mock)
    # Set form_submit_button to True to trigger the form submission
    stub_streamlit.form_submit_button.return_value = True
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    webui_instance.requirements_page()
    # Verify that st.error was called with the file not found message
    assert stub_streamlit.error.call_count > 0
    assert any('not found' in call[0][0] for call in stub_streamlit.error.call_args_list)
    # Verify that spec_cmd was not called
    spec_cmd_mock.assert_not_called()


def test_analysis_page_inspect_code_cmd_error_raises_error(stub_streamlit,
    monkeypatch):
    """Test error handling when inspect_code_cmd raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    # Mock inspect_code_cmd to raise an error
    inspect_code_cmd_mock = MagicMock(side_effect=RuntimeError(
        'Test inspect code error'))
    monkeypatch.setattr(
        'devsynth.application.cli.commands.inspect_code_cmd.inspect_code_cmd',
        inspect_code_cmd_mock)
    # Set form_submit_button to True to trigger the form submission
    stub_streamlit.form_submit_button.return_value = True
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    # Call the analysis_page method
    webui_instance.analysis_page()
    # Verify that display_result was called with the error message
    assert any('ERROR' in call[0][0] and 'Test inspect code error' in call[0][0] 
               for call in webui_instance.display_result.call_args_list)
    # Verify that inspect_code_cmd was called
    inspect_code_cmd_mock.assert_called_once()


def test_synthesis_page_test_cmd_error_raises_error(stub_streamlit, monkeypatch):
    """Test error handling when test_cmd raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    # Mock test_cmd to raise an error
    test_cmd_mock = MagicMock(side_effect=RuntimeError('Test test_cmd error'))
    monkeypatch.setattr('devsynth.application.cli.test_cmd', test_cmd_mock)
    # Set form_submit_button to True to trigger the form submission
    stub_streamlit.form_submit_button.return_value = True
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    # Call the synthesis_page method
    webui_instance.synthesis_page()
    # Verify that display_result was called with the error message
    assert any('ERROR' in call[0][0] and 'Test test_cmd error' in call[0][0] 
               for call in webui_instance.display_result.call_args_list)
    # Verify that test_cmd was called
    test_cmd_mock.assert_called_once()


def test_config_page_load_config_error_raises_error(stub_streamlit, monkeypatch):
    """Test error handling when load_project_config raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    # Mock load_project_config to raise an error
    load_config_mock = MagicMock(side_effect=RuntimeError(
        'Test load config error'))
    monkeypatch.setattr('devsynth.interface.webui.load_project_config',
        load_config_mock)
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    # Call the config_page method
    webui_instance.config_page()
    # Verify that display_result was called with the error message
    assert any('ERROR' in call[0][0] and 'Test load config error' in call[0][0] 
               for call in webui_instance.display_result.call_args_list)
    # Verify that load_project_config was called
    load_config_mock.assert_called_once()


def test_config_page_save_config_error_raises_error(stub_streamlit, monkeypatch):
    """Test error handling when save_config raises an exception.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    from devsynth.config import ProjectUnifiedConfig, ConfigModel
    # Create a mock config object
    mock_config = ProjectUnifiedConfig(
        config=ConfigModel(offline_mode=False, project_root='.', features={}), 
        path=Path('.'),
        use_pyproject=False
    )
    # Mock load_project_config to return the mock config
    monkeypatch.setattr(
        'devsynth.interface.webui.load_project_config',
        MagicMock(return_value=mock_config)
    )
    # Mock save_config to raise an error
    save_config_mock = MagicMock(side_effect=RuntimeError(
        'Test save config error'))
    monkeypatch.setattr(
        'devsynth.interface.webui.save_config',
        save_config_mock
    )
    # Set toggle and button to True to trigger the save action
    stub_streamlit.toggle.return_value = True
    stub_streamlit.button.return_value = True
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    # Call the config_page method
    webui_instance.config_page()
    # Verify that display_result was called with the error message
    assert any('ERROR' in call[0][0] and 'Test save config error' in call[0][0] 
               for call in webui_instance.display_result.call_args_list)
    # Verify that save_config was called
    save_config_mock.assert_called_once()
