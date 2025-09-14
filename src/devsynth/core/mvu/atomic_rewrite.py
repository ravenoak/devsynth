"""Utilities for rewriting Git history into atomic commits."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def cluster_commits_by_file(commits: Sequence[Any]) -> dict[str, list[Any]]:
    """Group commits by the files they modify.

    Parameters
    ----------
    commits:
        Sequence of commits ordered from oldest to newest.

    Returns
    -------
    dict[str, list[Any]]
        Mapping of file paths to commits that touched them.
    """

    clusters: dict[str, list[Any]] = {}
    for commit in commits:
        for path in commit.stats.files:
            clusters.setdefault(str(path), []).append(commit)
    return clusters


def rewrite_history(target_path: Path, branch_name: str, dry_run: bool = False) -> Any:
    """Create a new branch with the current history.

    Parameters
    ----------
    target_path:
        Path to the Git repository to rewrite.
    branch_name:
        Name of the new branch containing the rewritten history.
    dry_run:
        If ``True``, no changes are written and the repository is left untouched.

    Returns
    -------
    Repo
        The repository instance representing ``target_path``.
    """

    git = importlib.import_module("git")
    repo = git.Repo(str(target_path))
    if dry_run:
        return repo
    repo.git.branch(branch_name, "HEAD")
    return repo


__all__ = ["cluster_commits_by_file", "rewrite_history"]
