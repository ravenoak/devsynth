from unittest.mock import patch, MagicMock, call

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from devsynth.interface.cli import CLIUXBridge, CLIProgressIndicator


def test_cliuxbridge_ask_question():
    bridge = CLIUXBridge()
    with patch("rich.prompt.Prompt.ask", return_value="foo") as ask:
        result = bridge.ask_question("msg", choices=["a", "b"], default="a")
        # Check that the message is styled with the "prompt" style
        assert isinstance(ask.call_args[0][0], Text)
        assert ask.call_args[0][0].style == "prompt"
        assert str(ask.call_args[0][0]) == "msg"
        assert result == "foo"


def test_cliuxbridge_confirm_choice():
    bridge = CLIUXBridge()
    with patch("rich.prompt.Confirm.ask", return_value=True) as confirm:
        assert bridge.confirm_choice("proceed?", default=True)
        # Check that the message is styled with the "prompt" style
        assert isinstance(confirm.call_args[0][0], Text)
        assert confirm.call_args[0][0].style == "prompt"
        assert str(confirm.call_args[0][0]) == "proceed?"


def test_cliuxbridge_display_result_highlight():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("done", highlight=True)
        # Check that the message is wrapped in a Panel with "highlight" style
        assert isinstance(out.call_args[0][0], Panel)
        assert out.call_args[1]["style"] == "highlight"


def test_cliuxbridge_display_result_error():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("ERROR: Something went wrong", highlight=False)
        # Check that the message is styled with "error" style
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "ERROR: Something went wrong"
        assert out.call_args[0][0].style == "bold red"


def test_cliuxbridge_display_result_warning():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("WARNING: Be careful", highlight=False)
        # Check that the message is styled with "warning" style
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "WARNING: Be careful"
        assert out.call_args[0][0].style == "yellow"


def test_cliuxbridge_display_result_success():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("Task completed successfully", highlight=False)
        # Check that the message is styled with "success" style
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Task completed successfully"
        assert out.call_args[0][0].style == "green"


def test_cliuxbridge_display_result_heading():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("# Heading", highlight=False)
        # Check that the message is styled with "heading" style
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Heading"
        assert out.call_args[0][0].style == "bold blue"


def test_cliuxbridge_display_result_subheading():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("## Subheading", highlight=False)
        # Check that the message is styled with "subheading" style
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Subheading"
        assert out.call_args[0][0].style == "bold cyan"


def test_cliuxbridge_display_result_rich_markup():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("[bold]Bold text[/bold]", highlight=False)
        # Check that the message is passed through with Rich markup
        out.assert_called_once_with("[bold]Bold text[/bold]", highlight=False)


def test_cliuxbridge_display_result_normal():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("Normal message", highlight=False)
        # Check that the message is styled with no special style
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Normal message"
        assert out.call_args[0][0].style is None


def test_cliuxbridge_ask_question_validates_input():
    bridge = CLIUXBridge()
    with (
        patch("rich.prompt.Prompt.ask", return_value="bad") as ask,
        patch(
            "devsynth.interface.cli.validate_safe_input",
            side_effect=lambda x: f"clean-{x}",
        ) as validate,
    ):
        result = bridge.ask_question("msg")
        # Check that the message is styled with the "prompt" style
        assert isinstance(ask.call_args[0][0], Text)
        assert ask.call_args[0][0].style == "prompt"
        validate.assert_called_once_with("bad")
        assert result == "clean-bad"


def test_cliprogressindicator_subtasks():
    """Test the CLIProgressIndicator's subtask functionality."""
    # Create real objects instead of mocks to avoid MagicMock comparison issues
    console = Console(file=open("/dev/null", "w"))  # Redirect output to avoid clutter

    # Create a progress indicator
    indicator = CLIProgressIndicator(console, "Main task", 100)

    # Store the original _progress.add_task and _progress.update methods
    original_add_task = indicator._progress.add_task
    original_update = indicator._progress.update

    # Replace with our own tracking functions
    add_task_calls = []
    update_calls = []

    def mock_add_task(description, total=100):
        add_task_calls.append((description, total))
        return "mock_task_id"

    def mock_update(task_id, **kwargs):
        update_calls.append((task_id, kwargs))

    indicator._progress.add_task = mock_add_task
    indicator._progress.update = mock_update

    # Test add_subtask
    subtask_id = indicator.add_subtask("Subtask 1", 50)
    assert subtask_id == "mock_task_id"
    assert len(add_task_calls) == 1
    assert add_task_calls[0][1] == 50  # Check total
    assert "↳ Subtask 1" in add_task_calls[0][0]  # Check description contains the subtask name with arrow

    # Test update_subtask
    indicator.update_subtask(subtask_id, 10, "Updated subtask")
    assert len(update_calls) == 1
    assert update_calls[0][0] == subtask_id  # Check task_id
    assert update_calls[0][1]["advance"] == 10  # Check advance
    assert "↳ Updated subtask" in str(update_calls[0][1].get("description", ""))  # Check description with arrow

    # Test complete_subtask
    indicator.complete_subtask(subtask_id)
    assert len(update_calls) == 2
    assert update_calls[1][0] == subtask_id  # Check task_id
    assert update_calls[1][1]["completed"] is True  # Check completed flag

    # Test complete
    indicator.complete()
    assert len(update_calls) == 3
    assert update_calls[2][0] == indicator._task  # Check task_id
    assert update_calls[2][1]["completed"] is True  # Check completed flag

    # Clean up
    console.file.close()
