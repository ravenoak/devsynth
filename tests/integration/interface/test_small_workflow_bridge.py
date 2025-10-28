from typing import Union

import pytest

from devsynth.interface.agentapi import APIBridge
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import sanitize_output


class DummyProgress:
    """Progress indicator mirroring APIBridge behaviour."""

    def __init__(self, _console, description: str, total: int) -> None:
        self.description = sanitize_output(description)
        self.total = total
        self.current = 0
        self.messages = []
        self.messages.append(self.description)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.complete()
        return False

    def update(
        self, *, advance: float = 1, description: str | None = None
    ) -> None:
        if description:
            self.description = sanitize_output(description)
        self.current += advance
        self.messages.append(f"{self.description} ({self.current}/{self.total})")

    def complete(self) -> None:
        self.messages.append(f"{self.description} complete")


def small_workflow(bridge: CLIUXBridge | APIBridge) -> list[str]:
    """Minimal workflow exercising prompt, confirm and progress."""
    name = bridge.prompt("Name?", default="demo")
    if not bridge.confirm("Proceed?", default=True):
        bridge.print("cancelled")
        return []
    with bridge.create_progress("Working", total=2) as prog:
        prog.update()
        prog.update()
    bridge.print(f"Done {name}")
    msgs = getattr(bridge, "_test_messages", [])
    if isinstance(prog, DummyProgress):
        return prog.messages + msgs
    return msgs


def _setup_cli_bridge(monkeypatch) -> CLIUXBridge:
    answers = iter(["demo", True])
    monkeypatch.setattr(
        "devsynth.interface.cli.Prompt.ask", lambda *a, **k: next(answers)
    )
    monkeypatch.setattr(
        "devsynth.interface.cli.Confirm.ask", lambda *a, **k: next(answers)
    )
    out = []
    monkeypatch.setattr(
        "rich.console.Console.print",
        lambda self, msg, *, highlight=False, style=None: out.append(
            sanitize_output(msg)
        ),
    )
    monkeypatch.setattr("devsynth.interface.cli.CLIProgressIndicator", DummyProgress)
    bridge = CLIUXBridge()
    bridge._test_messages = out
    return bridge


@pytest.mark.medium
def test_cli_and_api_bridges_consistent_succeeds(monkeypatch):
    """Test that cli and api bridges consistent succeeds.

    ReqID: N/A"""
    cli_bridge = _setup_cli_bridge(monkeypatch)
    cli_msgs = small_workflow(cli_bridge)
    api_bridge = APIBridge(["demo", True])
    small_workflow(api_bridge)
    api_msgs = [m.split(" - ")[0] for m in api_bridge.messages]
    assert cli_msgs == api_msgs
