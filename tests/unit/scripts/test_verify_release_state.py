"""Tests for ``scripts/verify_release_state.py``. ReqID: FR-95"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import scripts.verify_release_state as verify_release_state

pytestmark = [pytest.mark.fast]


def setup_git_repo(root: Path) -> None:
    """Initialize a Git repository with one commit."""
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    dummy = root / "file.txt"
    dummy.write_text("content", encoding="utf-8")
    subprocess.run(
        ["git", "add", "file.txt"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True
    )


def create_release_file(
    root: Path, status: str, version: str = "0.1.0-alpha.1"
) -> Path:
    """Write a release file with the given status and version."""
    path = root / "release.md"
    path.write_text(
        f"---\nstatus: {status}\nversion: {version}\n---\n",
        encoding="utf-8",
    )
    return path


def patch_paths(
    monkeypatch: pytest.MonkeyPatch, root: Path, release_file: Path
) -> None:
    """Patch module paths to use temporary locations."""
    monkeypatch.setattr(verify_release_state, "ROOT", root)
    monkeypatch.setattr(verify_release_state, "RELEASE_FILE", release_file)
    monkeypatch.setattr(
        verify_release_state, "LOG_PATH", root / "dialectical_audit.log"
    )


def test_draft_status_missing_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Draft release without tag is allowed. ReqID: FR-95"""
    root = Path.cwd()
    setup_git_repo(root)
    release_file = create_release_file(root, status="draft")
    patch_paths(monkeypatch, root, release_file)
    assert verify_release_state.main() == 0


def test_published_status_without_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Published release without tag fails. ReqID: FR-95"""
    root = Path.cwd()
    setup_git_repo(root)
    release_file = create_release_file(root, status="published")
    patch_paths(monkeypatch, root, release_file)
    assert verify_release_state.main() == 1


def test_published_status_with_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Published release with tag is accepted. ReqID: FR-95"""
    root = Path.cwd()
    setup_git_repo(root)
    release_file = create_release_file(root, status="published")
    subprocess.run(
        ["git", "tag", "v0.1.0-alpha.1"], cwd=root, check=True, capture_output=True
    )
    patch_paths(monkeypatch, root, release_file)
    assert verify_release_state.main() == 0
