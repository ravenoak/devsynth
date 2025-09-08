"""Unit tests for CLI UX bridge non-interactive flows and logging branches.

ReqID: Phase 2 Section 5 (docs/plan.md); Tasks 5.1, 5.2 (docs/tasks.md)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from devsynth.interface.cli import CLIUXBridge


@pytest.mark.fast
def test_noninteractive_returns_defaults_and_logs(monkeypatch):
    """ask_question/confirm_choice should return defaults and log debug in non-interactive mode."""
    # Enable non-interactive mode
    monkeypatch.setenv("DEVSYNTH_NONINTERACTIVE", "1")

    # Capture logger calls on the module-level logger used by CLIUXBridge
    import devsynth.interface.cli as cli_mod

    debug_mock = MagicMock()
    monkeypatch.setattr(cli_mod.logger, "debug", debug_mock)

    # Create bridge
    bridge = CLIUXBridge()

    # ask_question should return default without prompting
    answer = bridge.ask_question("Pick one", choices=["a", "b"], default="a")
    assert answer == "a"

    # confirm_choice should return default
    confirmed = bridge.confirm_choice("Proceed?", default=True)
    assert confirmed is True

    # Ensure debug logs emitted for non-interactive path
    debug_calls = " ".join(" ".join(map(str, c.args)) for c in debug_mock.call_args_list)
    assert "Non-interactive mode" in debug_calls


@pytest.mark.fast
def test_display_result_logging_branches(monkeypatch):
    """display_result should use appropriate logging level and output; error path uses handler."""
    import devsynth.interface.cli as cli_mod

    # Patch logger methods to capture level usage
    debug_mock = MagicMock()
    info_mock = MagicMock()
    warn_mock = MagicMock()
    error_mock = MagicMock()
    monkeypatch.setattr(cli_mod.logger, "debug", debug_mock)
    monkeypatch.setattr(cli_mod.logger, "info", info_mock)
    monkeypatch.setattr(cli_mod.logger, "warning", warn_mock)
    monkeypatch.setattr(cli_mod.logger, "error", error_mock)

    # Patch console printing and formatting
    print_mock = MagicMock()
    monkeypatch.setattr("rich.console.Console.print", print_mock)

    # Patch SharedBridgeMixin formatter to a simple pass-through marker
    monkeypatch.setattr(
        "devsynth.interface.shared_bridge.SharedBridgeMixin._format_for_output",
        lambda self, message, *, highlight=False, message_type=None: f"FMT:{message}",
    )

    bridge = CLIUXBridge()

    # Warning branch
    bridge.display_result("warn-msg", message_type="warning")
    warn_mock.assert_called()  # logged at warning
    print_mock.assert_called()  # printed something
    args, kwargs = print_mock.call_args
    assert args[0] == "FMT:warn-msg"
    assert kwargs.get("style") in {"warning", None}  # style applied if theme supports

    print_mock.reset_mock()

    # Success (info) branch
    bridge.display_result("ok", message_type="success")
    info_mock.assert_called()
    args, kwargs = print_mock.call_args
    assert args[0] == "FMT:ok"
    assert kwargs.get("style") in {"success", None}

    print_mock.reset_mock()

    # Default (debug) branch
    bridge.display_result("plain")
    debug_mock.assert_called()
    args, kwargs = print_mock.call_args
    assert args[0] == "FMT:plain"

    print_mock.reset_mock()

    # Error branch should go through error handler and print formatted error
    # Patch error handler to return a sentinel formatted string
    bridge.error_handler.format_error = MagicMock(return_value="ERRFMT")
    bridge.display_result("oops", message_type="error")
    error_mock.assert_called()  # error logged
    print_mock.assert_called_with("ERRFMT")
