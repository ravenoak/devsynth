"""Utilities for rewriting Git history into atomic commits."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence

from git import Commit, Repo


def cluster_commits_by_file(commits: Sequence[Commit]) -> Dict[str, List[Commit]]:
    """Group commits by the files they modify.

    Parameters
    ----------
    commits:
        Sequence of commits ordered from oldest to newest.

    Returns
    -------
    Dict[str, List[Commit]]
        Mapping of file paths to commits that touched them.
    """

    clusters: Dict[str, List[Commit]] = {}
    for commit in commits:
        for path in commit.stats.files:
            clusters.setdefault(path, []).append(commit)
    return clusters


def rewrite_history(target_path: Path, branch_name: str, dry_run: bool = False) -> Repo:
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

    repo = Repo(str(target_path))
    if dry_run:
        return repo
    repo.git.branch(branch_name, "HEAD")
    return repo


__all__ = ["cluster_commits_by_file", "rewrite_history"]

