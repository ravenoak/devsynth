from unittest.mock import MagicMock, call, patch

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from devsynth.interface.cli import CLIProgressIndicator, CLIUXBridge


@pytest.fixture(autouse=True)
def disable_prompt_toolkit(monkeypatch):
    """Ensure prompt-toolkit integration is disabled for CLI UX bridge tests."""

    monkeypatch.setattr(
        "devsynth.interface.cli.get_prompt_toolkit_adapter", lambda: None
    )


@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


@pytest.mark.medium
def test_function(clean_state):
    # Test with clean state
    """Test that cliuxbridge ask question succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.prompt.Prompt.ask", return_value="foo") as ask:
        result = bridge.ask_question("msg", choices=["a", "b"], default="a")
        assert isinstance(ask.call_args[0][0], Text)
        assert ask.call_args[0][0].style == "prompt"
        assert str(ask.call_args[0][0]) == "msg"
        assert result == "foo"


@pytest.mark.medium
def test_cliuxbridge_confirm_choice_succeeds():
    """Test that cliuxbridge confirm choice succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.prompt.Confirm.ask", return_value=True) as confirm:
        assert bridge.confirm_choice("proceed?", default=True)
        assert isinstance(confirm.call_args[0][0], Text)
        assert confirm.call_args[0][0].style == "prompt"
        assert str(confirm.call_args[0][0]) == "proceed?"


@pytest.mark.medium
def test_cliuxbridge_display_result_highlight_succeeds():
    """Test that cliuxbridge display result highlight succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("done", highlight=True)
        assert isinstance(out.call_args[0][0], Panel)
        assert out.call_args[1]["style"] == "highlight"


@pytest.mark.medium
def test_cliuxbridge_display_result_error_succeeds():
    """Test that cliuxbridge display result error succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("Something went wrong", message_type="error")
        # Error messages are handled by handle_error, so we need to check what that prints
        # For now, let's check that console.print was called
        assert out.called


@pytest.mark.medium
def test_cliuxbridge_display_result_warning_succeeds():
    """Test that cliuxbridge display result warning succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("Be careful", message_type="warning")
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Be careful"
        assert out.call_args[0][0].style == "warning"


@pytest.mark.medium
def test_cliuxbridge_display_result_success_succeeds():
    """Test that cliuxbridge display result success succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("Task completed successfully", message_type="success")
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Task completed successfully"
        assert out.call_args[0][0].style == "success"


@pytest.mark.medium
def test_cliuxbridge_display_result_heading_succeeds():
    """Test that cliuxbridge display result heading succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("# Heading", highlight=False)
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Heading"
        assert out.call_args[0][0].style == "bold blue"


@pytest.mark.medium
def test_cliuxbridge_display_result_subheading_succeeds():
    """Test that cliuxbridge display result subheading succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("## Subheading", highlight=False)
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Subheading"
        assert out.call_args[0][0].style == "bold cyan"


@pytest.mark.fast
def test_cliuxbridge_set_colorblind_mode():
    """Test that colorblind mode can be enabled and disabled."""
    bridge = CLIUXBridge(colorblind_mode=False)
    assert not bridge.colorblind_mode

    bridge.set_colorblind_mode(True)
    assert bridge.colorblind_mode

    bridge.set_colorblind_mode(False)
    assert not bridge.colorblind_mode


@pytest.mark.fast
def test_cliuxbridge_show_completion():
    """Test that completion scripts are displayed."""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as mock_print:
        bridge.show_completion("#!/bin/bash\necho 'complete'")
        mock_print.assert_called_once()
        args = mock_print.call_args[0]
        assert len(args) >= 1


@pytest.mark.fast
def test_cliuxbridge_create_progress():
    """Test that progress indicators can be created."""
    bridge = CLIUXBridge()
    progress = bridge.create_progress("Testing", total=10)
    assert progress is not None
    # The progress object should be a CLIProgressIndicator
    from devsynth.interface.cli import CLIProgressIndicator
    assert isinstance(progress, CLIProgressIndicator)


@pytest.mark.medium
def test_cliuxbridge_display_result_rich_markup_succeeds():
    """Test that cliuxbridge display result rich markup succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("[bold]Bold text[/bold]", highlight=False)
        out.assert_called_once_with("[bold]Bold text[/bold]", highlight=False)


@pytest.mark.medium
def test_cliuxbridge_display_result_normal_succeeds():
    """Test that cliuxbridge display result normal succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("Normal message", highlight=False)
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Normal message"
        assert out.call_args[0][0].style is None


@pytest.mark.medium
def test_cliuxbridge_ask_question_validates_input_succeeds():
    """Test that cliuxbridge ask question validates input succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with (
        patch("rich.prompt.Prompt.ask", return_value="bad") as ask,
        patch(
            "devsynth.interface.cli.validate_safe_input",
            side_effect=lambda x: f"clean-{x}",
        ) as validate,
    ):
        result = bridge.ask_question("msg")
        assert isinstance(ask.call_args[0][0], Text)
        assert ask.call_args[0][0].style == "prompt"
        validate.assert_called_once_with("bad")
        assert result == "clean-bad"


@pytest.mark.medium
def test_cliprogressindicator_subtasks_succeeds(tmpdir):
    """Test the CLIProgressIndicator's subtask functionality.

    ReqID: N/A"""
    # Use tmpdir to create a temporary file instead of /dev/null
    temp_file = tmpdir.join("console_output.txt")

    # Use a StringIO object instead of a file for better isolation
    from io import StringIO

    output_stream = StringIO()
    console = Console(file=output_stream)
    indicator = CLIProgressIndicator(console, "Main task", 100)
    original_add_task = indicator._progress.add_task
    original_update = indicator._progress.update
    add_task_calls = []
    update_calls = []

    def mock_add_task(description, total=100):
        add_task_calls.append((description, total))
        return "mock_task_id"

    def mock_update(task_id, **kwargs):
        update_calls.append((task_id, kwargs))

    indicator._progress.add_task = mock_add_task
    indicator._progress.update = mock_update
    subtask_id = indicator.add_subtask("Subtask 1", 50)
    assert subtask_id == "mock_task_id"
    assert len(add_task_calls) == 1
    assert add_task_calls[0][1] == 50
    assert "↳ Subtask 1" in add_task_calls[0][0]
    indicator.update_subtask(subtask_id, 10, "Updated subtask")
    assert len(update_calls) == 1
    assert update_calls[0][0] == subtask_id
    assert update_calls[0][1]["advance"] == 10
    assert "↳ Updated subtask" in str(update_calls[0][1].get("description", ""))
    indicator.complete_subtask(subtask_id)
    assert len(update_calls) == 2
    assert update_calls[1][0] == subtask_id
    assert update_calls[1][1]["completed"] is True
    indicator.complete()
    assert len(update_calls) == 3
    assert update_calls[2][0] == indicator._task
    assert update_calls[2][1]["completed"] is True
    # Close the StringIO object
    output_stream.close()
