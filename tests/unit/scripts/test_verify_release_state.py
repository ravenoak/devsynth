"""Tests for ``scripts/verify_release_state.py``. ReqID: FR-95"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import scripts.verify_release_state as verify_release_state


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


def create_release_file(root: Path, status: str, version: str = "0.1.0a1") -> Path:
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


@pytest.mark.fast
def test_draft_status_missing_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Draft release without tag is allowed. ReqID: FR-95"""
    root = Path.cwd()
    setup_git_repo(root)
    release_file = create_release_file(root, status="draft")
    patch_paths(monkeypatch, root, release_file)
    assert verify_release_state.main() == 0


@pytest.mark.fast
def test_published_status_without_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Published release without tag fails. ReqID: FR-95"""
    root = Path.cwd()
    setup_git_repo(root)
    release_file = create_release_file(root, status="published")
    patch_paths(monkeypatch, root, release_file)
    assert verify_release_state.main() == 1


@pytest.mark.fast
def test_published_status_with_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Published release with tag is accepted. ReqID: FR-95"""
    root = Path.cwd()
    setup_git_repo(root)
    release_file = create_release_file(root, status="published")
    subprocess.run(
        ["git", "tag", "v0.1.0a1"], cwd=root, check=True, capture_output=True
    )
    patch_paths(monkeypatch, root, release_file)
    assert verify_release_state.main() == 0


@pytest.mark.fast
def test_parse_front_matter_returns_fields(tmp_path: Path) -> None:
    """The parser extracts YAML fields from the release document."""

    path = tmp_path / "release.md"
    path.write_text(
        "---\nstatus: review\nversion: 9.9.9\n---\nbody\n",
        encoding="utf-8",
    )
    data = verify_release_state.parse_front_matter(path)
    assert data == {"status": "review", "version": "9.9.9"}


@pytest.mark.fast
def test_parse_front_matter_without_header(tmp_path: Path) -> None:
    """Missing front matter yields an empty dictionary."""

    path = tmp_path / "release.md"
    path.write_text("no front matter\n", encoding="utf-8")
    assert verify_release_state.parse_front_matter(path) == {}


@pytest.mark.fast
def test_tag_exists_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return False when the tag is absent."""

    root = Path.cwd()
    setup_git_repo(root)
    monkeypatch.setattr(verify_release_state, "ROOT", root)
    assert not verify_release_state.tag_exists("v9.9.9")


@pytest.mark.fast
def test_tag_exists_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return True when the tag is present."""

    root = Path.cwd()
    setup_git_repo(root)
    subprocess.run(["git", "tag", "v9.9.9"], cwd=root, check=True, capture_output=True)
    monkeypatch.setattr(verify_release_state, "ROOT", root)
    assert verify_release_state.tag_exists("v9.9.9")


@pytest.mark.fast
def test_audit_is_clean_when_log_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing audit log is treated as clean."""

    log_path = Path.cwd() / "dialectical_audit.log"
    if log_path.exists():
        log_path.unlink()
    monkeypatch.setattr(verify_release_state, "LOG_PATH", log_path)
    assert verify_release_state.audit_is_clean()


@pytest.mark.fast
def test_audit_is_clean_with_unresolved_questions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unresolved questions block release verification."""

    log_path = Path.cwd() / "dialectical_audit.log"
    log_path.write_text(
        json.dumps({"questions": ["pending"], "resolved": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr(verify_release_state, "LOG_PATH", log_path)
    assert not verify_release_state.audit_is_clean()


@pytest.mark.fast
def test_audit_is_clean_with_only_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty questions list allows release verification."""

    log_path = Path.cwd() / "dialectical_audit.log"
    log_path.write_text(
        json.dumps({"questions": [], "resolved": ["done"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(verify_release_state, "LOG_PATH", log_path)
    assert verify_release_state.audit_is_clean()


@pytest.mark.fast
def test_audit_is_clean_with_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid JSON in the audit log fails the cleanliness check."""

    log_path = Path.cwd() / "dialectical_audit.log"
    log_path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(verify_release_state, "LOG_PATH", log_path)
    assert not verify_release_state.audit_is_clean()
