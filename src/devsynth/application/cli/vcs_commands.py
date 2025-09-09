"""Typer group for VCS (git) related commands."""

from __future__ import annotations

from typing import Optional

import typer

from devsynth.application.cli.commands.vcs_chunk_commit_cmd import (
    chunk_commit_cmd,
)
from devsynth.interface.ux_bridge import UXBridge

vcs_app = typer.Typer(help="VCS utilities")


@vcs_app.command("chunk-commit")
def chunk_commit(
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Show planned commit chunks and messages without executing by default",
    ),
    staged_only: bool = typer.Option(
        True,
        help=(
            "Operate only on staged changes (default). "
            "Disable to include unstaged changes."
        ),
    ),
    include_untracked: bool = typer.Option(
        False,
        help="When not --staged-only, include untracked files in grouping/commits.",
    ),
    no_verify: bool = typer.Option(
        False, help="Pass --no-verify to git commit for each chunk."
    ),
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Group repository changes into logical chunks and commit sequentially.

    This command inspects changed files, groups them into logical categories
    (e.g., docs, tests, src, config), and creates sequential commits per group.

    By default it runs in dry-run mode; pass --execute to perform commits.
    """
    chunk_commit_cmd(
        dry_run=dry_run,
        staged_only=staged_only,
        include_untracked=include_untracked,
        no_verify=no_verify,
        bridge=bridge,
    )


__all__ = ["vcs_app"]
