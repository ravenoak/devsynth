import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts import auto_issue_comment as mod


@pytest.mark.fast
def test_parse_issue_numbers_extracts_ids():
    assert mod.parse_issue_numbers("Fixes #12 and relates to #345") == [12, 345]


@pytest.mark.fast
def test_dry_run_when_env_missing(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    with patch.object(mod, "get_commit_message", return_value=("deadbeef", "ref #1")):
        rc = mod.main(["--dry-run"])  # also works without envs
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry-run" in out


@pytest.mark.fast
def test_posts_comment_when_env_present(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    with patch.object(mod, "get_commit_message", return_value=("sha", "ref #7")):
        with patch.object(
            mod,
            "post_comment",
            return_value=(201, "ok", {"x-ratelimit-remaining": "4998"}),
        ) as pc:
            rc = mod.main([])
    assert rc == 0
    pc.assert_called_once()
    out = capsys.readouterr().out
    assert "commented on #7" in out
