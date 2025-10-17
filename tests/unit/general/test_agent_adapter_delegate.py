from unittest.mock import MagicMock

import click
import pytest
import typer
from click.testing import CliRunner

import devsynth.adapters.cli.typer_adapter as typer_adapter
from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.domain.models.wsde_facade import WSDETeam


@pytest.mark.medium
def test_delegate_task_single_agent_succeeds():
    """Test that delegate task single agent succeeds.

    ReqID: N/A"""
    coord = WSDETeamCoordinator()
    coord.create_team("t")
    agent = MagicMock()
    agent.process.return_value = {"result": "ok"}
    coord.add_agent(agent)
    result = coord.delegate_task({"description": "do"})
    assert result["result"] == "ok"
    agent.process.assert_called_once_with({"description": "do"})


@pytest.mark.medium
def test_delegate_task_multi_agent_succeeds():
    """Test that delegate task multi agent succeeds.

    ReqID: N/A"""
    coord = WSDETeamCoordinator()
    coord.create_team("team")
    a1 = MagicMock()
    a1.process.return_value = {"result": "a"}
    a2 = MagicMock()
    a2.process.return_value = {"result": "b"}
    coord.add_agents([a1, a2])
    team = coord.get_team("team")
    team.select_primus_by_expertise = MagicMock()
    team.get_primus = MagicMock(return_value=a1)
    team.add_solution = MagicMock()
    team.build_consensus = MagicMock(
        return_value={
            "result": "final",
            "initial_preferences": {"a1": 0.8, "a2": 0.9},
            "explanation": "Consensus reached",
            "status": "success",
            "rounds": [],
            "final_preferences": {"a1": 0.8, "a2": 0.9},
        }
    )
    team.apply_enhanced_dialectical_reasoning_multi = MagicMock(
        return_value={"eval": "ok"}
    )
    task = {"type": "code"}
    result = coord.delegate_task(task)
    team.select_primus_by_expertise.assert_called_once_with(task)
    assert result["result"] == "final"
    assert result["dialectical_analysis"] == {"eval": "ok"}


@pytest.mark.medium
def test_parse_args_runs_succeeds(monkeypatch):
    """Test that parse args runs succeeds.

    ReqID: N/A"""
    executed = {}
    app = typer.Typer()

    @app.command()
    def hello():
        executed["run"] = True

    @app.command()
    def bye():
        pass

    monkeypatch.setattr(typer_adapter, "build_app", lambda: app)
    monkeypatch.setattr(
        typer_adapter,
        "_warn_if_features_disabled",
        lambda: executed.setdefault("warn", True),
    )
    runner = CliRunner()
    cmd = click.Command("cmd", callback=lambda: typer_adapter.parse_args(["hello"]))
    result = runner.invoke(cmd, [])
    assert result.exit_code == 0
    assert executed["run"] and executed["warn"]


@pytest.mark.medium
def test_show_help_lists_groups(monkeypatch):
    """Show help outputs group names without errors."""
    app = typer.Typer()
    sub = typer.Typer()

    @sub.command()
    def foo():
        pass

    app.add_typer(sub, name="group")

    monkeypatch.setattr(typer_adapter, "build_app", lambda: app)
    runner = CliRunner()
    cmd = click.Command("cmd", callback=typer_adapter.show_help)
    result = runner.invoke(cmd, [])
    assert result.exit_code == 0
    assert "group" in result.stdout


@pytest.mark.medium
def test_show_help_fallback_registered_typers(monkeypatch):
    """Show help works when only registered_typers is available."""
    app = typer.Typer()
    sub = typer.Typer()

    @sub.command()
    def foo():
        pass

    app.add_typer(sub, name="group")

    class OldApp:
        def __init__(self, a):
            self.registered_commands = a.registered_commands
            self.registered_typers = [(sub, "group")]
            self.info = a.info

    monkeypatch.setattr(typer_adapter, "build_app", lambda: OldApp(app))
    runner = CliRunner()
    cmd = click.Command("cmd", callback=typer_adapter.show_help)
    result = runner.invoke(cmd, [])
    assert result.exit_code == 0
    assert "group" in result.stdout
