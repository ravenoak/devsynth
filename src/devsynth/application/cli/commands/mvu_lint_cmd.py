"""CLI command to lint commit messages for MVUU compliance."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from devsynth.core.mvu.linter import lint_commit_message, lint_range
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


def mvu_lint_cmd(
    message_file: Path | None = typer.Option(
        None,
        "--message-file",
        help="Path to commit message file to lint.",
    ),
    rev_range: str = typer.Option(
        "origin/main..HEAD",
        "--range",
        help="Git revision range to lint, e.g. origin/main..HEAD.",
    ),
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Lint commit messages for MVUU compliance."""
    ux_bridge = bridge or CLIUXBridge()
    if message_file is not None:
        message = message_file.read_text(encoding="utf-8")
        errors = lint_commit_message(message)
    else:
        errors = lint_range(rev_range)
    if errors:
        ux_bridge.print("\n\n".join(errors))
        raise typer.Exit(code=1)
    ux_bridge.print("[green]All commit messages valid[/green]")
