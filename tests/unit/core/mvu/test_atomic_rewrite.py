from __future__ import annotations

from pathlib import Path

from git import Repo

from devsynth.core.mvu.atomic_rewrite import cluster_commits_by_file


def _commit(repo: Repo, path: Path, content: str, message: str) -> None:
    path.write_text(content, encoding="utf-8")
    repo.index.add([path.name])
    repo.index.commit(message)


def test_cluster_commits_by_file(tmp_path) -> None:
    repo = Repo.init(tmp_path, initial_branch="main")
    _commit(repo, tmp_path / "a.txt", "a", "a")
    _commit(repo, tmp_path / "b.txt", "b", "b")
    (tmp_path / "a.txt").write_text("aa", encoding="utf-8")
    (tmp_path / "b.txt").write_text("bb", encoding="utf-8")
    repo.index.add(["a.txt", "b.txt"])
    repo.index.commit("ab")

    commits = list(repo.iter_commits("HEAD", reverse=True))
    clusters = cluster_commits_by_file(commits)

    assert set(clusters) == {"a.txt", "b.txt"}
    assert [c.message.strip() for c in clusters["a.txt"]] == ["a", "ab"]
    assert [c.message.strip() for c in clusters["b.txt"]] == ["b", "ab"]

