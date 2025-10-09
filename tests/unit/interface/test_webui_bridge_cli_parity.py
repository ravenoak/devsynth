"""Ensure the WebUI bridge mirrors CLI defaults for prompts and confirmations."""

from __future__ import annotations

import pytest

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.webui_bridge import WebUIBridge

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("force_webui_available")]


def test_webui_bridge_matches_cli_prompt_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-interactive prompts should align between CLI and WebUI bridges."""

    monkeypatch.setattr("devsynth.interface.cli._non_interactive", lambda: True)

    cli_bridge = CLIUXBridge()
    web_bridge = WebUIBridge()

    cases = [
        ("Favorite tool?", "DevSynth", "DevSynth"),
        ("Preferred workflow?", "Test-First", "Test-First"),
        ("Optional answer", None, ""),
    ]

    for message, default, expected in cases:
        assert web_bridge.ask_question(message, default=default) == expected
        assert cli_bridge.ask_question(message, default=default) == expected

    for default in (True, False):
        assert web_bridge.confirm_choice("Continue?", default=default) is default
        assert cli_bridge.confirm_choice("Continue?", default=default) is default
