from unittest.mock import patch

from devsynth.interface.cli import CLIUXBridge


def test_cliuxbridge_ask_question():
    bridge = CLIUXBridge()
    with patch("rich.prompt.Prompt.ask", return_value="foo") as ask:
        result = bridge.ask_question("msg", choices=["a", "b"], default="a")
        ask.assert_called_once()
        assert result == "foo"


def test_cliuxbridge_confirm_choice():
    bridge = CLIUXBridge()
    with patch("rich.prompt.Confirm.ask", return_value=True) as confirm:
        assert bridge.confirm_choice("proceed?", default=True)
        confirm.assert_called_once()


def test_cliuxbridge_display_result():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("done", highlight=True)
        out.assert_called_once_with("done", highlight=True)


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
        ask.assert_called_once_with(
            "msg",
            choices=None,
            default=None,
            show_default=True,
        )
        validate.assert_called_once_with("bad")
        assert result == "clean-bad"
