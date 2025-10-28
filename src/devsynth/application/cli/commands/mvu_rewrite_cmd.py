"""CLI command to rewrite Git history into atomic commits."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from devsynth.core.mvu.atomic_rewrite import rewrite_history
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


def mvu_rewrite_cmd(
    target_path: Path = typer.Option(
        Path("."),
        "--path",
        help="Path to the repository to rewrite.",
    ),
    branch_name: str = typer.Option(
        "atomic",
        "--branch-name",
        help="Name of the branch for rewritten history.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Perform analysis without writing changes.",
    ),
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Rewrite commit history into atomic commits."""

    ux_bridge = bridge or CLIUXBridge()
    rewrite_history(target_path, branch_name, dry_run=dry_run)
    if dry_run:
        ux_bridge.print("[yellow]Dry run complete[/yellow]")
    else:
        ux_bridge.print(f"[green]Rewritten history to branch '{branch_name}'[/green]")
