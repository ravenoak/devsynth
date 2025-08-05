from __future__ import annotations

from devsynth.core.mvu.models import MVUU
from devsynth.core.mvu.report import TraceRecord, generate_report


def _records() -> list[TraceRecord]:
    mvuu = MVUU(
        utility_statement="util",
        affected_files=["a.py"],
        tests=["test_a.py"],
        TraceID="TID",
        mvuu=True,
        issue="ISSUE-1",
    )
    return [TraceRecord(commit="abcdef1", mvuu=mvuu)]


def test_generate_report_markdown(monkeypatch) -> None:
    monkeypatch.setattr(
        "devsynth.core.mvu.report.scan_history", lambda since: _records()
    )
    out = generate_report(fmt="markdown")
    assert "| TraceID |" in out
    assert "abcdef1"[:7] in out


def test_generate_report_html(monkeypatch) -> None:
    monkeypatch.setattr(
        "devsynth.core.mvu.report.scan_history", lambda since: _records()
    )
    out = generate_report(fmt="html")
    assert "<table>" in out
    assert "<td>TID</td>" in out
