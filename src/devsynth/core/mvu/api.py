"""Query API for MVUU metadata."""

from __future__ import annotations

import subprocess
from datetime import datetime
from functools import lru_cache
from typing import Iterator, List, Tuple

from devsynth.adapters.issues import GitHubIssueAdapter, JiraIssueAdapter
from devsynth.core.config_loader import load_config

from .models import MVUU
from .parser import parse_commit_message
from .storage import read_commit_message


@lru_cache(maxsize=1)
def _issue_adapters() -> dict[str, object]:
    """Instantiate issue adapters based on configuration."""
    cfg = load_config().mvuu or {}
    issues_cfg = cfg.get("issues", {})
    adapters = {}
    gh = issues_cfg.get("github")
    if gh and gh.get("token") and gh.get("base_url"):
        adapters["github"] = GitHubIssueAdapter(gh["base_url"], gh["token"])
    jr = issues_cfg.get("jira")
    if jr and jr.get("token") and jr.get("base_url"):
        adapters["jira"] = JiraIssueAdapter(jr["base_url"], jr["token"])
    return adapters


def _enrich_mvuu(mvuu: MVUU) -> None:
    """Populate MVUU with external issue metadata when available."""
    adapters = _issue_adapters()
    trace = mvuu.TraceID
    meta = None
    if trace.startswith("#") and "github" in adapters:
        meta = adapters["github"].fetch(trace)  # type: ignore[attr-defined]
    elif "-" in trace and "jira" in adapters:
        meta = adapters["jira"].fetch(trace)  # type: ignore[attr-defined]
    if meta:
        mvuu.issue_title = meta.get("title")
        mvuu.acceptance_criteria = meta.get("acceptance_criteria")


def iter_mvuu_commits(
    ref: str = "HEAD", enrich: bool = False
) -> Iterator[Tuple[str, MVUU]]:
    """Yield commits containing MVUU metadata starting from ``ref``.

    Args:
        ref: Git reference to start from.
        enrich: When ``True``, populate MVUU entries with external issue metadata.
    """
    revs = subprocess.check_output(["git", "rev-list", ref], text=True)
    for commit in revs.strip().splitlines():
        try:
            message = read_commit_message(commit)
            mvuu = parse_commit_message(message)
        except Exception:
            continue
        if enrich:
            _enrich_mvuu(mvuu)
        yield commit, mvuu


def get_by_trace_id(
    trace_id: str, ref: str = "HEAD", *, enrich: bool = False
) -> List[Tuple[str, MVUU]]:
    """Return commits whose MVUU TraceID matches ``trace_id``.

    Args:
        trace_id: Trace identifier to search for.
        ref: Git reference to start from.
        enrich: When ``True``, populate MVUU entries with external issue metadata.
    """
    return [
        (commit, mvuu)
        for commit, mvuu in iter_mvuu_commits(ref, enrich=enrich)
        if mvuu.TraceID == trace_id
    ]


def get_by_affected_path(
    path: str, ref: str = "HEAD", *, enrich: bool = False
) -> List[Tuple[str, MVUU]]:
    """Return commits whose MVUU affected files include ``path``.

    Args:
        path: File path to search for.
        ref: Git reference to start from.
        enrich: When ``True``, populate MVUU entries with external issue metadata.
    """
    return [
        (commit, mvuu)
        for commit, mvuu in iter_mvuu_commits(ref, enrich=enrich)
        if path in mvuu.affected_files
    ]


def get_by_date_range(
    start: datetime, end: datetime, ref: str = "HEAD", *, enrich: bool = False
) -> List[Tuple[str, MVUU]]:
    """Return commits within a date range containing MVUU metadata.

    Args:
        start: Start of date range.
        end: End of date range.
        ref: Git reference to search.
        enrich: When ``True``, populate MVUU entries with external issue metadata.
    """
    revs = subprocess.check_output(
        [
            "git",
            "log",
            "--since",
            start.isoformat(),
            "--until",
            end.isoformat(),
            "--format=%H",
            ref,
        ],
        text=True,
    )
    commits = revs.strip().splitlines()
    results: List[Tuple[str, MVUU]] = []
    for commit in commits:
        try:
            message = read_commit_message(commit)
            mvuu = parse_commit_message(message)
        except Exception:
            continue
        if enrich:
            _enrich_mvuu(mvuu)
        results.append((commit, mvuu))
    return results
