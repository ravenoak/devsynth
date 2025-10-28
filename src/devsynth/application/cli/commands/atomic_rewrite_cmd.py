"""[experimental] Atomic-Rewrite baseline CLI command (feature-gated).

This provides a minimal workflow stub for atomic commit rewriting. Advanced
paths remain behind the "atomic_rewrite" feature flag.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from devsynth.core.feature_flags import is_enabled
from devsynth.core.mvu.atomic_rewrite import rewrite_history
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


def atomic_rewrite_cmd(
    target_path: Path = typer.Option(
        Path("."), "--path", help="Path to the repository to rewrite.", exists=True
    ),
    branch_name: str = typer.Option(
        "atomic", "--branch-name", help="Name of the branch for rewritten history."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Perform analysis without writing changes."
    ),
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Run minimal Atomic‑Rewrite flow.

    This command is feature-gated. Enable with:
        devsynth config enable-feature atomic_rewrite
    """
    ux = bridge or CLIUXBridge()

    if not is_enabled("atomic_rewrite"):
        ux.print(
            "[yellow]Atomic‑Rewrite is disabled. Enable with: 'devsynth config enable-feature atomic_rewrite'.[/yellow]"
        )
        raise typer.Exit(2)

    # Minimal baseline: call underlying helper in dry-run or branch mode
    repo = rewrite_history(target_path, branch_name, dry_run=dry_run)
    if dry_run:
        ux.print(
            f"[green]Atomic‑Rewrite dry run successful for repo at '{repo.working_dir}'.[/green]"
        )
    else:
        ux.print(
            f"[green]Atomic‑Rewrite completed. New branch created: '{branch_name}'.[/green]"
        )


__all__ = ["atomic_rewrite_cmd"]
