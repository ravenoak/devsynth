import importlib
import sys
import time
from unittest.mock import MagicMock

import pytest

from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Provide a mocked ``streamlit`` module."""
    st = _mock_streamlit()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


@pytest.fixture
def clean_state():
    """Provide a clean state for each test."""
    yield


@pytest.mark.medium
def test_ui_progress_init_succeeds(mock_streamlit, clean_state):
    """Test the initialization of ``_UIProgress``.

    ReqID: N/A"""
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    progress = bridge.create_progress("Test Progress", total=100)

    assert progress._description == "Test Progress"
    assert progress._total == 100
    assert progress._current == 0
    assert progress._subtasks == {}
    assert mock_streamlit.empty.called
    assert mock_streamlit.progress.called
    status_container = mock_streamlit.empty.return_value
    status_container.markdown.assert_called_with("**Test Progress** - 0%")


@pytest.mark.medium
def test_ui_progress_update_succeeds(mock_streamlit, clean_state):
    """Test the update method of ``_UIProgress``.

    ReqID: N/A"""
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    progress = bridge.create_progress("Test Progress", total=100)

    status_container = mock_streamlit.empty.return_value
    status_container.markdown.reset_mock()
    progress_bar = mock_streamlit.progress.return_value
    progress_bar.progress.reset_mock()

    progress.update(advance=25, description="Updated Progress")

    assert progress._current == 25
    assert progress._description == "Updated Progress"
    status_container.markdown.assert_called_with("**Updated Progress** - 25%")
    progress_bar.progress.assert_called_with(0.25)


@pytest.mark.medium
def test_ui_progress_complete_succeeds(mock_streamlit, clean_state):
    """Test the complete method of ``_UIProgress``.

    ReqID: N/A"""
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    progress = bridge.create_progress("Test Progress", total=100)
    progress.complete()

    assert progress._current == 100
    mock_streamlit.success.assert_called_with("Completed: Test Progress")


@pytest.mark.medium
def test_ui_progress_add_subtask_succeeds(mock_streamlit, clean_state):
    """Test the ``add_subtask`` method of ``_UIProgress``.

    ReqID: N/A"""
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    progress = bridge.create_progress("Test Progress", total=100)
    subtask_id = progress.add_subtask("Subtask 1", total=50)

    assert subtask_id in progress._subtasks
    assert progress._subtasks[subtask_id]["description"] == "Subtask 1"
    assert progress._subtasks[subtask_id]["total"] == 50
    assert progress._subtasks[subtask_id]["current"] == 0
    assert mock_streamlit.container.called
    subtask_container = mock_streamlit.container.return_value.__enter__.return_value
    subtask_container.markdown.assert_called_with(
        "&nbsp;&nbsp;&nbsp;&nbsp;**Subtask 1** - 0%"
    )


@pytest.mark.medium
def test_ui_progress_update_subtask_succeeds(mock_streamlit, clean_state):
    """Test the ``update_subtask`` method of ``_UIProgress``.

    ReqID: N/A"""
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    progress = bridge.create_progress("Test Progress", total=100)
    subtask_id = progress.add_subtask("Subtask 1", total=50)

    subtask_container = mock_streamlit.container.return_value.__enter__.return_value
    subtask_container.markdown.reset_mock()
    subtask_progress_bar = subtask_container.progress.return_value
    subtask_progress_bar.progress.reset_mock()

    progress.update_subtask(subtask_id, advance=25, description="Updated Subtask")

    assert progress._subtasks[subtask_id]["current"] == 25
    assert progress._subtasks[subtask_id]["description"] == "Updated Subtask"
    subtask_container.markdown.assert_called_with(
        "&nbsp;&nbsp;&nbsp;&nbsp;**Updated Subtask** - 50%"
    )
    subtask_progress_bar.progress.assert_called_with(0.5)


@pytest.mark.medium
def test_ui_progress_complete_subtask_succeeds(mock_streamlit, clean_state):
    """Test the ``complete_subtask`` method of ``_UIProgress``.

    ReqID: N/A"""
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    progress = bridge.create_progress("Test Progress", total=100)
    subtask_id = progress.add_subtask("Subtask 1", total=50)
    progress.complete_subtask(subtask_id)

    assert progress._subtasks[subtask_id]["current"] == 50
    subtask_container = mock_streamlit.container.return_value.__enter__.return_value
    subtask_container.markdown.assert_called_with(
        "&nbsp;&nbsp;&nbsp;&nbsp;**Subtask 1** - 100%"
    )
    subtask_progress_bar = subtask_container.progress.return_value
    subtask_progress_bar.progress.assert_called_with(1.0)
    subtask_container.success.assert_called_with("Completed: Subtask 1")


@pytest.mark.fast
def test_ui_progress_eta_displays_seconds_when_under_minute(
    mock_streamlit, monkeypatch, clean_state
):
    """Render ETA in seconds when less than a minute remains."""

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    times = iter([0.0, 5.0, 10.0])

    def fake_time() -> float:
        return next(times)

    monkeypatch.setattr(time, "time", fake_time)

    status_container = MagicMock()
    time_container = MagicMock()
    mock_streamlit.empty.side_effect = [status_container, time_container]

    bridge = WebUI()
    progress = bridge.create_progress("ETA Seconds", total=100)
    mock_streamlit.empty.side_effect = None

    status_container.markdown.reset_mock()
    time_container.empty.reset_mock()
    time_container.info.reset_mock()

    progress.update(advance=20)

    time_container.info.assert_called_once_with("ETA: 20 seconds")


@pytest.mark.fast
def test_ui_progress_eta_displays_minutes_when_under_hour(
    mock_streamlit, monkeypatch, clean_state
):
    """Render ETA rounded to whole minutes when under an hour remains."""

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    times = iter([0.0, 100.0, 200.0])

    def fake_time() -> float:
        return next(times)

    monkeypatch.setattr(time, "time", fake_time)

    status_container = MagicMock()
    time_container = MagicMock()
    mock_streamlit.empty.side_effect = [status_container, time_container]

    bridge = WebUI()
    progress = bridge.create_progress("ETA Minutes", total=100)
    mock_streamlit.empty.side_effect = None

    status_container.markdown.reset_mock()
    time_container.empty.reset_mock()
    time_container.info.reset_mock()

    progress.update(advance=10)

    time_container.info.assert_called_once_with("ETA: 15 minutes")


@pytest.mark.fast
def test_ui_progress_eta_displays_hours_and_minutes(
    mock_streamlit, monkeypatch, clean_state
):
    """Render ETA with hours and minutes when exceeding an hour."""

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    times = iter([0.0, 100.0, 200.0])

    def fake_time() -> float:
        return next(times)

    monkeypatch.setattr(time, "time", fake_time)

    status_container = MagicMock()
    time_container = MagicMock()
    mock_streamlit.empty.side_effect = [status_container, time_container]

    bridge = WebUI()
    progress = bridge.create_progress("ETA Hours", total=100)
    mock_streamlit.empty.side_effect = None

    status_container.markdown.reset_mock()
    time_container.empty.reset_mock()
    time_container.info.reset_mock()

    progress.update(advance=1)

    time_container.info.assert_called_once_with("ETA: 2 hours, 45 minutes")


@pytest.mark.fast
def test_ui_progress_status_transitions_without_explicit_status(
    mock_streamlit, monkeypatch, clean_state
):
    """Ensure automatic status text transitions at documented thresholds."""

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    times = iter([0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0])

    def fake_time() -> float:
        return next(times)

    monkeypatch.setattr(time, "time", fake_time)

    status_container = MagicMock()
    time_container = MagicMock()
    mock_streamlit.empty.side_effect = [status_container, time_container]

    bridge = WebUI()
    progress = bridge.create_progress("Status Thresholds", total=100)
    mock_streamlit.empty.side_effect = None

    time_container.empty.reset_mock()
    time_container.info.reset_mock()

    increments = [10, 15, 25, 25, 24, 1]
    expected_statuses = [
        "Starting...",
        "Processing...",
        "Halfway there...",
        "Almost done...",
        "Finalizing...",
        "Complete",
    ]

    observed_statuses = []
    for advance, expected in zip(increments, expected_statuses, strict=True):
        progress.update(advance=advance)
        observed_statuses.append(progress._status)
        assert progress._status == expected

    assert observed_statuses == expected_statuses
    time_container.empty.assert_called()


@pytest.mark.fast
def test_ui_progress_subtasks_update_with_frozen_time(
    mock_streamlit, monkeypatch, clean_state
):
    """Subtask updates still render when the clock is frozen."""

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    monkeypatch.setattr(time, "time", lambda: 100.0)

    status_container = MagicMock()
    time_container = MagicMock()
    mock_streamlit.empty.side_effect = [status_container, time_container]

    bridge = WebUI()
    progress = bridge.create_progress("Frozen Subtasks", total=100)
    mock_streamlit.empty.side_effect = None

    subtask_container = mock_streamlit.container.return_value.__enter__.return_value
    subtask_bar = subtask_container.progress.return_value

    subtask_container.markdown.reset_mock()
    subtask_bar.progress.reset_mock()

    subtask_id = progress.add_subtask("Subtask", total=20)

    subtask_container.markdown.assert_called_with(
        "&nbsp;&nbsp;&nbsp;&nbsp;**Subtask** - 0%"
    )
    subtask_bar.progress.assert_called_with(0.0)

    subtask_container.markdown.reset_mock()
    subtask_bar.progress.reset_mock()

    progress.update_subtask(subtask_id, advance=10, description="Updated Subtask")

    subtask_container.markdown.assert_called_with(
        "&nbsp;&nbsp;&nbsp;&nbsp;**Updated Subtask** - 50%"
    )
    subtask_bar.progress.assert_called_with(0.5)
