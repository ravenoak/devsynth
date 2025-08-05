"""Generate MVU traceability reports from git history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .api import iter_mvuu_commits
from .models import MVUU


@dataclass
class TraceRecord:
    """MVU traceability record associated with a commit."""

    commit: str
    mvuu: MVUU


def scan_history(since: str | None = None) -> List[TraceRecord]:
    """Return MVU records starting from ``since`` until ``HEAD``.

    Args:
        since: Optional git revision to start scanning from. When ``None``, the
            entire commit history reachable from ``HEAD`` is scanned.

    Returns:
        List of :class:`TraceRecord` objects in chronological order.
    """

    rev = "HEAD" if since is None else f"{since}..HEAD"
    commits = list(iter_mvuu_commits(rev))
    commits.reverse()  # oldest first for reporting
    return [TraceRecord(commit=c, mvuu=m) for c, m in commits]


def _markdown_table(records: Iterable[TraceRecord]) -> str:
    """Return a Markdown table for ``records``."""

    headers = [
        "TraceID",
        "Utility Statement",
        "Affected Files",
        "Tests",
        "Issue",
        "Commit",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + " | ".join(["---"] * len(headers)) + "|",
    ]
    for rec in records:
        mvuu = rec.mvuu
        lines.append(
            "| {tid} | {util} | {files} | {tests} | {issue} | {commit} |".format(
                tid=mvuu.TraceID,
                util=mvuu.utility_statement,
                files=", ".join(mvuu.affected_files),
                tests=", ".join(mvuu.tests),
                issue=mvuu.issue,
                commit=rec.commit[:7],
            )
        )
    return "\n".join(lines) + "\n"


def _html_table(records: Iterable[TraceRecord]) -> str:
    """Return an HTML table for ``records``."""

    lines = [
        "<table>",
        "  <thead>",
        "    <tr><th>TraceID</th><th>Utility Statement</th><th>Affected Files</th><th>Tests</th><th>Issue</th><th>Commit</th></tr>",
        "  </thead>",
        "  <tbody>",
    ]
    for rec in records:
        mvuu = rec.mvuu
        lines.append(
            "    <tr><td>{tid}</td><td>{util}</td><td>{files}</td><td>{tests}</td><td>{issue}</td><td>{commit}</td></tr>".format(
                tid=mvuu.TraceID,
                util=mvuu.utility_statement,
                files=", ".join(mvuu.affected_files),
                tests=", ".join(mvuu.tests),
                issue=mvuu.issue,
                commit=rec.commit[:7],
            )
        )
    lines.extend(["  </tbody>", "</table>"])
    return "\n".join(lines)


def generate_report(since: str | None = None, fmt: str = "markdown") -> str:
    """Generate a traceability report.

    Args:
        since: Optional git revision to start scanning from.
        fmt: Output format, ``"markdown"`` or ``"html"``.

    Returns:
        Report content as a string.
    """

    records = scan_history(since)
    if fmt.lower() == "html":
        return _html_table(records)
    return _markdown_table(records)
