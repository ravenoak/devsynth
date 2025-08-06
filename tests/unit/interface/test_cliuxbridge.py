from unittest.mock import patch, MagicMock, call
import pytest
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
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
        bridge.display_result("ERROR: Something went wrong", highlight=False)
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "ERROR: Something went wrong"
        assert out.call_args[0][0].style == "bold red"


@pytest.mark.medium
def test_cliuxbridge_display_result_warning_succeeds():
    """Test that cliuxbridge display result warning succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("WARNING: Be careful", highlight=False)
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "WARNING: Be careful"
        assert out.call_args[0][0].style == "yellow"


@pytest.mark.medium
def test_cliuxbridge_display_result_success_succeeds():
    """Test that cliuxbridge display result success succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("Task completed successfully", highlight=False)
        assert isinstance(out.call_args[0][0], Text)
        assert str(out.call_args[0][0]) == "Task completed successfully"
        assert out.call_args[0][0].style == "green"


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
