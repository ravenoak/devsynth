"""Integration test for MVU enrichment using issue adapters."""

from __future__ import annotations

import subprocess
from pathlib import Path

import responses

from devsynth.core import mvu


def _init_repo(path: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=path)
    subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=path)
    subprocess.check_call(["git", "config", "user.name", "Test User"], cwd=path)


@responses.activate
def test_get_by_trace_id_enriches(tmp_path, monkeypatch) -> None:
    """get_by_trace_id attaches issue metadata when configured."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    cfg_dir = repo / ".devsynth"
    cfg_dir.mkdir()
    cfg_dir.joinpath("mvu.yml").write_text(
        """schema: docs/specifications/mvuuschema.json
storage:
  path: db.json
  format: json
issues:
  github:
    base_url: https://api.github.com/repos/org/repo
    token: token
""",
        encoding="utf-8",
    )
    mvuu_data = mvu.MVUU(
        utility_statement="test",
        affected_files=["file.txt"],
        tests=["pytest"],
        TraceID="#1",
        mvuu=True,
        issue="#1",
    )
    message = "feat: add file\n\n" + mvu.format_mvuu_footer(mvuu_data)
    (repo / "file.txt").write_text("content", encoding="utf-8")
    subprocess.check_call(["git", "add", "file.txt"], cwd=repo)
    subprocess.check_call(["git", "commit", "-m", message], cwd=repo)

    responses.add(
        responses.GET,
        "https://api.github.com/repos/org/repo/issues/1",
        json={"title": "Issue 1", "body": "AC"},
        status=200,
    )

    monkeypatch.chdir(repo)
    results = mvu.get_by_trace_id("#1", enrich=True)
    assert results
    mvuu_loaded = results[0][1]
    assert getattr(mvuu_loaded, "issue_title") == "Issue 1"
    assert getattr(mvuu_loaded, "acceptance_criteria") == "AC"
