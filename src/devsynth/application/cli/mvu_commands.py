"""Typer group for MVU related commands."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer

from devsynth.application.cli.commands.mvu_exec_cmd import mvu_exec_cmd
from devsynth.application.cli.commands.mvu_init_cmd import mvu_init_cmd
from devsynth.application.cli.commands.mvu_lint_cmd import mvu_lint_cmd
from devsynth.application.cli.commands.mvu_report_cmd import mvu_report_cmd
from devsynth.application.cli.commands.mvu_rewrite_cmd import mvu_rewrite_cmd
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge

mvu_app = typer.Typer(help="MVU utilities")


@mvu_app.command("init")
def init_cmd(*, bridge: UXBridge | None = None) -> None:
    mvu_init_cmd(bridge=bridge)


@mvu_app.command("lint")
def lint_cmd(*, bridge: UXBridge | None = None) -> None:
    mvu_lint_cmd(bridge=bridge)


@mvu_app.command("report")
def report_cmd(
    since: str | None = typer.Option(None, help="Git revision to scan"),
    fmt: str = typer.Option("markdown", help="Output format"),
    output: Path | None = typer.Option(None, help="Optional output path"),
    *,
    bridge: UXBridge | None = None,
) -> None:
    mvu_report_cmd(since=since, fmt=fmt, output=output, bridge=bridge)


@mvu_app.command("rewrite")
def rewrite_cmd(
    target_path: Path = typer.Option(Path("."), exists=True, file_okay=False),
    branch_name: str = typer.Option("atomic", help="Target branch name"),
    dry_run: bool = typer.Option(False, help="Print actions without executing"),
    *,
    bridge: UXBridge | None = None,
) -> None:
    mvu_rewrite_cmd(
        target_path=target_path, branch_name=branch_name, dry_run=dry_run, bridge=bridge
    )


@mvu_app.command("exec")
def exec_cmd(
    command: list[str] = typer.Argument(
        ..., help="Shell command to run", allow_dash=True
    ),
    *,
    bridge: UXBridge | None = None,
) -> None:
    bridge = bridge or CLIUXBridge()
    code = mvu_exec_cmd(command, bridge=bridge)
    raise typer.Exit(code)


__all__ = ["mvu_app"]
