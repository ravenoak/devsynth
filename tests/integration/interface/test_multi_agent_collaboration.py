import types
from typing import Union

import pytest

from devsynth.application.collaboration.collaborative_wsde_team import (
    CollaborativeWSDETeam,
)
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.interface.agentapi import APIBridge
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import sanitize_output


class DummyProgress:
    """Progress indicator mimicking APIBridge behaviour."""

    def __init__(self, _console, description: str, total: int) -> None:
        self.description = sanitize_output(description)
        self.total = total
        self.current = 0
        self.messages = [self.description]

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


class VoteAgent:
    """Simple agent returning a predefined vote."""

    def __init__(self, name: str, vote: str) -> None:
        self.name = name
        self.vote = vote
        self.current_role = None
        self.expertise = []
        self.config = types.SimpleNamespace(name=name, parameters={})

    def process(self, task):
        return {"vote": self.vote}


def collaborative_vote_workflow(bridge: CLIUXBridge | APIBridge) -> list[str]:
    """Run a minimal multi-agent voting workflow through a UX bridge."""

    team = WSDETeam(name="Team")
    names = [bridge.ask_question("Agent name?", default=f"a{i + 1}") for i in range(3)]
    votes = [bridge.ask_question("Vote?", default="x") for _ in range(3)]
    agents = [VoteAgent(n, v) for n, v in zip(names, votes)]
    team.add_agents(agents)
    team.select_primus_by_expertise({"domain": "demo"})

    task = {
        "type": "critical_decision",
        "is_critical": True,
        "domain": "demo",
        "options": [{"id": "x"}, {"id": "y"}],
    }

    with bridge.create_progress("Voting", total=1) as prog:
        result = team.vote_on_critical_decision(task)
        prog.update()

    bridge.display_result(f"Winner {result['result']['winner']}")

    progress_msgs = getattr(prog, "messages", getattr(prog, "_messages", []))
    progress_msgs = [m.split(" - ")[0] for m in progress_msgs]

    if isinstance(bridge, APIBridge):
        remaining = bridge.messages[len(progress_msgs) :]
        sanitized = [m.split(" - ")[0] for m in remaining]
        return progress_msgs + sanitized

    msgs = getattr(bridge, "_test_messages", [])
    return progress_msgs + msgs


def _setup_cli_bridge(monkeypatch) -> CLIUXBridge:
    answers = iter(["a1", "x", "a2", "y", "a3", "y"])
    monkeypatch.setattr(
        "devsynth.interface.cli.Prompt.ask", lambda *a, **k: next(answers)
    )
    out = []
    monkeypatch.setattr(
        "rich.console.Console.print",
        lambda self, msg, *, highlight=False, style=None: out.append(
            sanitize_output(str(msg))
        ),
    )
    monkeypatch.setattr("devsynth.interface.cli.CLIProgressIndicator", DummyProgress)
    bridge = CLIUXBridge()
    bridge._test_messages = out
    return bridge


@pytest.mark.medium
def test_cli_and_api_bridges_multi_agent_consistent(monkeypatch):
    """Test that CLI and API bridges behave the same for multi-agent collaboration."""

    cli_bridge = _setup_cli_bridge(monkeypatch)
    cli_msgs = collaborative_vote_workflow(cli_bridge)

    api_bridge = APIBridge(["a1", "x", "a2", "y", "a3", "y"])
    api_msgs = collaborative_vote_workflow(api_bridge)

    assert cli_msgs == api_msgs


class SimpleAgent:
    def __init__(self, name, expertise=None):
        self.name = name
        self.expertise = expertise or []
        self.current_role = None
        self.config = types.SimpleNamespace(name=name, parameters={})

    def process(self, task):
        return {}


@pytest.mark.medium
def test_vote_with_role_reassignment_succeeds():
    team = CollaborativeWSDETeam(name="VoteTestTeam")
    agents = [
        SimpleAgent("a1", ["security"]),
        SimpleAgent("a2", ["testing"]),
        SimpleAgent("a3", ["security"]),
    ]
    team.add_agents(agents)

    task = {
        "id": "decision1",
        "type": "critical_decision",
        "is_critical": True,
        "domain": "security",
        "options": ["A", "B"],
    }

    result = team.vote_with_role_reassignment(task)
    assert result["status"] == "completed"
    assert result["result"] in task["options"]
    assert team.role_history[-1]["task_id"] == task["id"]
    assert team.get_primus().name in {"a1", "a3"}


@pytest.mark.medium
def test_dynamic_role_reassignment_changes_primus():
    team = CollaborativeWSDETeam(name="RoleChangeTeam")
    agents = [
        SimpleAgent("a1", ["security"]),
        SimpleAgent("a2", ["testing"]),
        SimpleAgent("a3", ["security"]),
    ]
    team.add_agents(agents)

    team.dynamic_role_reassignment({"domain": "security"})
    first = team.get_primus().name
    team.dynamic_role_reassignment({"domain": "testing"})
    second = team.get_primus().name

    assert first != second
