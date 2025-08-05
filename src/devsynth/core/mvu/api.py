"""Query API for MVUU metadata."""

from __future__ import annotations

import subprocess
from datetime import datetime
from typing import Iterator, List, Tuple

from .models import MVUU
from .parser import parse_commit_message
from .storage import read_commit_message


def iter_mvuu_commits(ref: str = "HEAD") -> Iterator[Tuple[str, MVUU]]:
    """Yield commits containing MVUU metadata starting from ``ref``."""
    revs = subprocess.check_output(["git", "rev-list", ref], text=True)
    for commit in revs.strip().splitlines():
        try:
            message = read_commit_message(commit)
            mvuu = parse_commit_message(message)
        except Exception:
            continue
        yield commit, mvuu


def get_by_trace_id(trace_id: str, ref: str = "HEAD") -> List[Tuple[str, MVUU]]:
    """Return commits whose MVUU TraceID matches ``trace_id``."""
    return [
        (commit, mvuu)
        for commit, mvuu in iter_mvuu_commits(ref)
        if mvuu.TraceID == trace_id
    ]


def get_by_affected_path(path: str, ref: str = "HEAD") -> List[Tuple[str, MVUU]]:
    """Return commits whose MVUU affected files include ``path``."""
    return [
        (commit, mvuu)
        for commit, mvuu in iter_mvuu_commits(ref)
        if path in mvuu.affected_files
    ]


def get_by_date_range(
    start: datetime, end: datetime, ref: str = "HEAD"
) -> List[Tuple[str, MVUU]]:
    """Return commits within a date range containing MVUU metadata."""
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
        results.append((commit, mvuu))
    return results
