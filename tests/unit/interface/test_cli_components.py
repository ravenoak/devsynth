from unittest.mock import patch, MagicMock, call
import pytest
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from devsynth.interface.cli import CLIUXBridge, CLIProgressIndicator


@pytest.mark.medium
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


@pytest.mark.slow
def test_function(clean_state):
    # Test with clean state
    """Test the create_progress method of CLIUXBridge.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("devsynth.interface.cli.CLIProgressIndicator") as mock_indicator:
        progress = bridge.create_progress("Test progress", total=50)
        mock_indicator.assert_called_once_with(bridge.console, "Test progress", 50)


@pytest.mark.medium
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


@pytest.mark.slow
def test_cliprogressindicator_update_succeeds(clean_state):
    """Test the update method of CLIProgressIndicator.

    ReqID: N/A"""
    console = MagicMock()
    progress_mock = MagicMock(spec=ClassName)
    with patch("rich.progress.Progress", return_value=progress_mock):
        indicator = CLIProgressIndicator(console, "Main task", 100)
        indicator.update(advance=5)
        progress_mock.update.assert_called_with(
            indicator._task, advance=5, description=None
        )
        indicator.update(advance=10, description="Updated task")
        progress_mock.update.assert_called_with(
            indicator._task, advance=10, description="Updated task"
        )


@pytest.mark.slow
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


def test_cliprogressindicator_sanitize_output_succeeds(clean_state):
    """Test that CLIProgressIndicator sanitizes output.

    ReqID: N/A"""
    console = MagicMock()
    progress_mock = MagicMock(spec=ClassName)
    with patch("rich.progress.Progress", return_value=progress_mock):
        with patch(
            "devsynth.interface.cli.sanitize_output",
            side_effect=lambda x: f"sanitized-{x}",
        ):
            indicator = CLIProgressIndicator(console, "Main task", 100)
            progress_mock.add_task.assert_called_with("sanitized-Main task", total=100)
            indicator.update(description="<script>alert('xss')</script>")
            progress_mock.update.assert_called_with(
                indicator._task,
                advance=1,
                description="sanitized-<script>alert('xss')</script>",
            )
            progress_mock.add_task.reset_mock()
            progress_mock.add_task.return_value = "subtask1"
            subtask_id = indicator.add_subtask("<img src=x onerror=alert('xss')>", 50)
            progress_mock.add_task.assert_called_with(
                "  ↳ sanitized-<img src=x onerror=alert('xss')>", total=50
            )
            indicator.update_subtask(
                subtask_id, description="<iframe src=javascript:alert('xss')>"
            )
            progress_mock.update.assert_called_with(
                subtask_id,
                advance=1,
                description="  ↳ sanitized-<iframe src=javascript:alert('xss')>",
            )


@pytest.mark.medium
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


def test_cliprogressindicator_multiple_subtasks_succeeds(clean_state):
    """Test handling of multiple subtasks in CLIProgressIndicator.

    ReqID: N/A"""
    console = MagicMock()
    progress_mock = MagicMock(spec=ClassName)
    with patch("rich.progress.Progress", return_value=progress_mock):
        indicator = CLIProgressIndicator(console, "Main task", 100)
        progress_mock.add_task.side_effect = ["subtask1", "subtask2", "subtask3"]
        subtask1 = indicator.add_subtask("Subtask 1", 30)
        subtask2 = indicator.add_subtask("Subtask 2", 40)
        subtask3 = indicator.add_subtask("Subtask 3", 50)
        assert subtask1 == "subtask1"
        assert subtask2 == "subtask2"
        assert subtask3 == "subtask3"
        assert progress_mock.add_task.call_count == 4
        assert progress_mock.add_task.call_args_list[1] == call(
            "  ↳ Subtask 1", total=30
        )
        assert progress_mock.add_task.call_args_list[2] == call(
            "  ↳ Subtask 2", total=40
        )
        assert progress_mock.add_task.call_args_list[3] == call(
            "  ↳ Subtask 3", total=50
        )
        indicator.update_subtask(subtask2, 20)
        indicator.complete_subtask(subtask1)
        indicator.update_subtask(subtask3, 25)
        indicator.complete_subtask(subtask3)
        indicator.complete_subtask(subtask2)
        assert progress_mock.update.call_args_list[0] == call(
            subtask2, advance=20, description=None
        )
        assert progress_mock.update.call_args_list[1] == call(subtask1, completed=True)
        assert progress_mock.update.call_args_list[2] == call(
            subtask3, advance=25, description=None
        )
        assert progress_mock.update.call_args_list[3] == call(subtask3, completed=True)
        assert progress_mock.update.call_args_list[4] == call(subtask2, completed=True)


@pytest.mark.medium
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


def test_cliuxbridge_display_result_heading_levels_succeeds(clean_state):
    """Test handling of different heading levels in display_result.


    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("# Level 1 Heading")
        out.assert_called_with("Level 1 Heading", style="heading")
        bridge.display_result("## Level 2 Heading")
        out.assert_called_with("Level 2 Heading", style="subheading")
        bridge.display_result("### Level 3 Heading")
        out.assert_called_with("Level 3 Heading", style="subheading")
        bridge.display_result("#### Level 4 Heading")
        out.assert_called_with("Level 4 Heading", style="subheading")
        bridge.display_result("##### Level 5 Heading")
        out.assert_called_with("Level 5 Heading", style="subheading")
        bridge.display_result("###### Level 6 Heading")
        out.assert_called_with("Level 6 Heading", style="subheading")


@pytest.mark.medium
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


def test_cliuxbridge_display_result_smart_styling_succeeds(clean_state):
    """Test smart styling based on message content in display_result.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("ERROR: Something went wrong")
        out.assert_called_with("ERROR: Something went wrong", style="error")
        bridge.display_result("FAILED: Operation could not be completed")
        out.assert_called_with(
            "FAILED: Operation could not be completed", style="error"
        )
        bridge.display_result("WARNING: This is a warning message")
        out.assert_called_with("WARNING: This is a warning message", style="warning")
        bridge.display_result("SUCCESS: Operation completed")
        out.assert_called_with("SUCCESS: Operation completed", style="success")
        bridge.display_result("Task completed successfully")
        out.assert_called_with("Task completed successfully", style="success")
        bridge.display_result("This is a regular message")
        out.assert_called_with("This is a regular message", style=None)


@pytest.mark.medium
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


def test_cliuxbridge_display_result_rich_markup_succeeds(clean_state):
    """Test processing of Rich markup in display_result.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("This is [bold red]important[/bold red] information")
        out.assert_called_with(
            "This is [bold red]important[/bold red] information", highlight=False
        )
        bridge.display_result(
            "This is [bold blue]highlighted[/bold blue] text", highlight=True
        )
        out.assert_called_with(
            "This is [bold blue]highlighted[/bold blue] text", highlight=True
        )


@pytest.mark.medium
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


def test_cliuxbridge_display_result_highlight_succeeds(clean_state):
    """Test styling based on the highlight flag in display_result.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        with patch("rich.panel.Panel") as panel_mock:
            panel_mock.return_value = "PANEL:Important message"
            bridge.display_result("Important message", highlight=True)
            panel_mock.assert_called_with("Important message", style="highlight")
            out.assert_called_with("PANEL:Important message")
            bridge.display_result("Regular message", highlight=False)
            out.assert_called_with("Regular message", style=None)
            panel_mock.return_value = "PANEL:Info message"
            bridge.display_result("Info message", highlight=True)
            panel_mock.assert_called_with("Info message", style="highlight")
            out.assert_called_with("PANEL:Info message")
