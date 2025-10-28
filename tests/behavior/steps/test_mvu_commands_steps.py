from pathlib import Path
from typing import List

import pytest
import typer
from pytest_bdd import given, parsers, scenarios, then, when
from typer import Typer
from typer.testing import CliRunner

from devsynth.application.cli.commands.mvu_exec_cmd import mvu_exec_cmd
from devsynth.application.cli.commands.mvu_init_cmd import mvu_init_cmd
from devsynth.application.cli.commands.mvu_lint_cmd import mvu_lint_cmd
from devsynth.application.cli.commands.mvu_report_cmd import mvu_report_cmd
from devsynth.application.cli.commands.mvu_rewrite_cmd import mvu_rewrite_cmd
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]


def _app() -> Typer:
    app = Typer()
    mvu = Typer()

    def _init_wrapper() -> None:
        mvu_init_cmd()

    def _lint_wrapper() -> None:
        mvu_lint_cmd()

    def _report_wrapper(
        since: str | None = None, fmt: str = "markdown", output: Path | None = None
    ) -> None:
        mvu_report_cmd(since=since, fmt=fmt, output=output)

    def _rewrite_wrapper(
        target_path: Path = Path("."),
        branch_name: str = "atomic",
        dry_run: bool = False,
    ) -> None:
        mvu_rewrite_cmd(
            target_path=target_path, branch_name=branch_name, dry_run=dry_run
        )

    def _exec_wrapper(command: list[str] = typer.Argument(..., allow_dash=True)):
        code = mvu_exec_cmd(command)
        raise typer.Exit(code)

    mvu.command("init")(_init_wrapper)
    mvu.command("lint")(_lint_wrapper)
    mvu.command("report")(_report_wrapper)
    mvu.command("rewrite")(_rewrite_wrapper)
    mvu.command("exec")(_exec_wrapper)
    app.add_typer(mvu, name="mvu")
    return app


scenarios(feature_path(__file__, "general", "commands.feature"))


@given("the DevSynth CLI is installed")
def devsynth_cli_installed() -> bool:
    return True


@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_project_dir):
    return tmp_project_dir


@given("MVU rewrite completes successfully")
def mvu_rewrite_stub(monkeypatch) -> None:
    monkeypatch.setattr(
        "devsynth.application.cli.commands.mvu_rewrite_cmd.rewrite_history",
        lambda *args, **kwargs: None,
    )


@when(parsers.parse('I run the command "{command}"'))
def run_mvu_command(command: str, command_context):
    args = command.split()
    if args[0] == "devsynth":
        args = args[1:]
    runner = CliRunner()
    result = runner.invoke(_app(), args)
    command_context["output"] = result.output
    command_context["exit_code"] = result.exit_code


@then("the command should succeed")
def command_should_succeed(command_context) -> None:
    assert command_context.get("exit_code") == 0


@then(parsers.parse('the output should contain "{text}"'))
def output_should_contain(text: str, command_context) -> None:
    assert text in command_context.get("output", "")


@then('the file ".devsynth/mvu.yml" should exist')
def mvu_file_exists() -> None:
    assert Path(".devsynth/mvu.yml").exists()
