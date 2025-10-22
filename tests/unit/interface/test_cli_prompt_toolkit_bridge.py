"""CLI bridge integration tests for the prompt-toolkit adapter."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from rich.text import Text

from devsynth.interface.cli import CLIUXBridge


pytestmark = [pytest.mark.fast]


def test_cli_ask_question_uses_prompt_toolkit(monkeypatch: pytest.MonkeyPatch) -> None:
    """ask_question should delegate to the adapter when available."""

    bridge = CLIUXBridge()
    adapter = MagicMock()
    adapter.prompt_text.return_value = "picked"
    monkeypatch.setattr(
        "devsynth.interface.cli.get_prompt_toolkit_adapter", lambda: adapter
    )
    monkeypatch.setattr(
        "devsynth.interface.cli.validate_safe_input", lambda value: f"safe-{value}"
    )

    result = bridge.ask_question(
        "Select option", choices=["alpha", "beta"], default="alpha"
    )

    adapter.prompt_text.assert_called_once_with(
        "Select option", choices=["alpha", "beta"], default="alpha", show_default=True
    )
    assert result == "safe-picked"


def test_cli_confirm_choice_uses_prompt_toolkit(monkeypatch: pytest.MonkeyPatch) -> None:
    """confirm_choice should return the adapter's boolean response."""

    bridge = CLIUXBridge()
    adapter = MagicMock()
    adapter.confirm.return_value = True
    monkeypatch.setattr(
        "devsynth.interface.cli.get_prompt_toolkit_adapter", lambda: adapter
    )

    assert bridge.confirm_choice("Proceed?", default=False) is True
    adapter.confirm.assert_called_once_with("Proceed?", default=False)


def test_cli_prompt_fallback_to_rich(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the adapter is unavailable the Rich prompt path is used."""

    bridge = CLIUXBridge()
    monkeypatch.setattr(
        "devsynth.interface.cli.get_prompt_toolkit_adapter", lambda: None
    )

    calls: list[tuple[str, dict[str, object]]] = []

    def fake_ask(message, **kwargs):
        calls.append((message, kwargs))
        return "typed"

    monkeypatch.setattr("rich.prompt.Prompt.ask", fake_ask)
    monkeypatch.setattr(
        "devsynth.interface.cli.validate_safe_input", lambda value: value
    )

    bridge.ask_question("Fallback", default="typed")

    assert calls and isinstance(calls[0][0], Text)
