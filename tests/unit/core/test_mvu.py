"""Tests for MVUU core utilities."""

from __future__ import annotations

import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from devsynth.core import mvu

pytestmark = [pytest.mark.fast]


def _init_repo(path: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=path)
    subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=path)
    subprocess.check_call(["git", "config", "user.name", "Test User"], cwd=path)


def test_schema_has_required_fields() -> None:
    """Schema should expose required top-level properties."""
    assert "utility_statement" in mvu.MVUU_SCHEMA["properties"]


def test_end_to_end_mvu_flow(tmp_path: Path, monkeypatch) -> None:
    """MVUU data can be parsed, validated, stored, and queried."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    mvuu_data = mvu.MVUU(
        utility_statement="test",
        affected_files=["file.txt"],
        tests=["pytest"],
        TraceID="DSY-1234",
        mvuu=True,
        issue="#1234",
    )
    message = "feat: add file\n\n" + mvu.format_mvuu_footer(mvuu_data)
    (repo / "file.txt").write_text("content", encoding="utf-8")
    subprocess.check_call(["git", "add", "file.txt"], cwd=repo)
    subprocess.check_call(["git", "commit", "-m", message], cwd=repo)

    monkeypatch.chdir(repo)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

    mvuu_loaded = mvu.read_mvuu_from_commit(commit)
    assert mvuu_loaded is not None
    assert mvuu_loaded.TraceID == "DSY-1234"
    assert mvu.validate_affected_files(mvuu_loaded, ["file.txt"]) == []

    assert mvu.get_by_trace_id("DSY-1234")
    assert mvu.get_by_affected_path("file.txt")
    now = datetime.utcnow()
    results = mvu.get_by_date_range(now - timedelta(days=1), now + timedelta(days=1))
    assert results
