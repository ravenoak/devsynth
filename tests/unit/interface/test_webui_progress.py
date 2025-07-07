import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, call

import pytest

from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Fixture to mock streamlit for testing."""
    st = _mock_streamlit()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


def test_ui_progress_init(mock_streamlit):
    """Test the initialization of _UIProgress."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Create a progress indicator
    progress = bridge.create_progress("Test Progress", total=100)
    
    # Verify that the progress indicator was created with the correct description
    assert progress._description == "Test Progress"
    assert progress._total == 100
    assert progress._current == 0
    assert progress._subtasks == {}
    
    # Verify that the status container was created
    assert mock_streamlit.empty.called
    
    # Verify that the progress bar was created
    assert mock_streamlit.progress.called
    
    # Verify that the initial display was updated
    status_container = mock_streamlit.empty.return_value
    status_container.markdown.assert_called_with("**Test Progress** - 0%")


def test_ui_progress_update(mock_streamlit):
    """Test the update method of _UIProgress."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Create a progress indicator
    progress = bridge.create_progress("Test Progress", total=100)
    
    # Reset the mock to clear the initialization calls
    status_container = mock_streamlit.empty.return_value
    status_container.markdown.reset_mock()
    progress_bar = mock_streamlit.progress.return_value
    progress_bar.progress.reset_mock()
    
    # Update the progress
    progress.update(advance=25, description="Updated Progress")
    
    # Verify that the progress was updated
    assert progress._current == 25
    assert progress._description == "Updated Progress"
    
    # Verify that the display was updated
    status_container.markdown.assert_called_with("**Updated Progress** - 25%")
    progress_bar.progress.assert_called_with(0.25)


def test_ui_progress_complete(mock_streamlit):
    """Test the complete method of _UIProgress."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Create a progress indicator
    progress = bridge.create_progress("Test Progress", total=100)
    
    # Complete the progress
    progress.complete()
    
    # Verify that the progress was completed
    assert progress._current == 100
    
    # Verify that the success message was displayed
    mock_streamlit.success.assert_called_with("Completed: Test Progress")


def test_ui_progress_add_subtask(mock_streamlit):
    """Test the add_subtask method of _UIProgress."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Create a progress indicator
    progress = bridge.create_progress("Test Progress", total=100)
    
    # Add a subtask
    subtask_id = progress.add_subtask("Subtask 1", total=50)
    
    # Verify that the subtask was added
    assert subtask_id in progress._subtasks
    assert progress._subtasks[subtask_id]["description"] == "Subtask 1"
    assert progress._subtasks[subtask_id]["total"] == 50
    assert progress._subtasks[subtask_id]["current"] == 0
    
    # Verify that the subtask container was created
    assert mock_streamlit.container.called
    
    # Verify that the subtask display was updated
    subtask_container = mock_streamlit.container.return_value.__enter__.return_value
    subtask_container.markdown.assert_called_with("&nbsp;&nbsp;&nbsp;&nbsp;**Subtask 1** - 0%")


def test_ui_progress_update_subtask(mock_streamlit):
    """Test the update_subtask method of _UIProgress."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Create a progress indicator
    progress = bridge.create_progress("Test Progress", total=100)
    
    # Add a subtask
    subtask_id = progress.add_subtask("Subtask 1", total=50)
    
    # Reset the mock to clear the initialization calls
    subtask_container = mock_streamlit.container.return_value.__enter__.return_value
    subtask_container.markdown.reset_mock()
    subtask_progress_bar = subtask_container.progress.return_value
    subtask_progress_bar.progress.reset_mock()
    
    # Update the subtask
    progress.update_subtask(subtask_id, advance=25, description="Updated Subtask")
    
    # Verify that the subtask was updated
    assert progress._subtasks[subtask_id]["current"] == 25
    assert progress._subtasks[subtask_id]["description"] == "Updated Subtask"
    
    # Verify that the subtask display was updated
    subtask_container.markdown.assert_called_with("&nbsp;&nbsp;&nbsp;&nbsp;**Updated Subtask** - 50%")
    subtask_progress_bar.progress.assert_called_with(0.5)


def test_ui_progress_complete_subtask(mock_streamlit):
    """Test the complete_subtask method of _UIProgress."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Create a progress indicator
    progress = bridge.create_progress("Test Progress", total=100)
    
    # Add a subtask
    subtask_id = progress.add_subtask("Subtask 1", total=50)
    
    # Complete the subtask
    progress.complete_subtask(subtask_id)
    
    # Verify that the subtask was completed
    assert progress._subtasks[subtask_id]["current"] == 50
    
    # Verify that the subtask display was updated
    subtask_container = mock_streamlit.container.return_value.__enter__.return_value
    subtask_container.markdown.assert_called_with("&nbsp;&nbsp;&nbsp;&nbsp;**Subtask 1** - 100%")
    subtask_progress_bar = subtask_container.progress.return_value
    subtask_progress_bar.progress.assert_called_with(1.0)
    
    # Verify that the success message was displayed
    subtask_container.success.assert_called_with("Completed: Subtask 1")