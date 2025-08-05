from __future__ import annotations

from pathlib import Path

from git import Repo

from devsynth.core.mvu.atomic_rewrite import rewrite_history


def _commit(repo: Repo, path: Path, content: str, message: str) -> None:
    path.write_text(content, encoding="utf-8")
    repo.index.add([path.name])
    repo.index.commit(message)


def test_atomic_rewrite_round_trip(tmp_path) -> None:
    repo_path = tmp_path / "repo"
    repo = Repo.init(repo_path, initial_branch="main")
    _commit(repo, repo_path / "one.txt", "1", "one")
    _commit(repo, repo_path / "two.txt", "2", "two")

    repo = rewrite_history(repo_path, "atomic")

    diff = repo.git.diff("atomic", "main")
    assert diff == ""

