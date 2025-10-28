"""Typer group for VCS (git) related commands."""

from __future__ import annotations

from typing import Optional

import typer

from devsynth.application.cli.commands.vcs_chunk_commit_cmd import (
    chunk_commit_cmd,
)
from devsynth.application.cli.commands.vcs_fix_rebase_pr_cmd import (
    fix_rebase_pr_cmd,
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


@vcs_app.command("fix-rebase-pr")
def fix_rebase_pr(
    base_branch: str = typer.Option(
        "main",
        "--base-branch",
        help="Base branch (target of the PR), e.g., 'main'",
    ),
    source_branch: str = typer.Option(
        "release-prep",
        "--source-branch",
        help="Source branch to salvage (e.g., 'release-prep')",
    ),
    remote: str = typer.Option(
        "origin",
        "--remote",
        help="Git remote name",
    ),
    new_branch: str | None = typer.Option(
        None,
        "--new-branch",
        help="Optional new branch name; defaults to '<source>-fix-<timestamp>'",
    ),
    execute: bool = typer.Option(
        False,
        "--execute/--dry-run",
        help="Execute the plan (default: dry-run)",
    ),
    push: bool = typer.Option(
        False,
        "--push",
        help="If executing, also push the new branch to the remote",
    ),
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Recreate a mergeable PR branch by cherry-picking unique commits onto base.

    Use this when GitHub refuses to rebase-merge an already-rebased branch.
    """
    fix_rebase_pr_cmd(
        base_branch=base_branch,
        source_branch=source_branch,
        remote=remote,
        new_branch=new_branch,
        execute=execute,
        push=push,
        bridge=bridge,
    )


__all__ = ["vcs_app"]
