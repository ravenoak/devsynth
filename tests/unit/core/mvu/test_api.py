from __future__ import annotations

import pytest

from devsynth.core.mvu.api import get_by_affected_path, get_by_trace_id
from devsynth.core.mvu.models import MVUU

pytestmark = [pytest.mark.fast]


def _iter_stub(ref: str, enrich: bool = False):
    mvuu1 = MVUU(
        utility_statement="u1",
        affected_files=["a.py"],
        tests=["test_a.py"],
        TraceID="T1",
        mvuu=True,
        issue="ISSUE-1",
    )
    mvuu2 = MVUU(
        utility_statement="u2",
        affected_files=["b.py"],
        tests=["test_b.py"],
        TraceID="T2",
        mvuu=True,
        issue="ISSUE-2",
    )
    return [("c1", mvuu1), ("c2", mvuu2)]


def test_get_by_trace_id(monkeypatch) -> None:
    monkeypatch.setattr(
        "devsynth.core.mvu.api.iter_mvuu_commits",
        lambda ref, enrich=False: _iter_stub(ref, enrich),
    )
    res = get_by_trace_id("T1")
    assert len(res) == 1
    assert res[0][1].TraceID == "T1"


def test_get_by_affected_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "devsynth.core.mvu.api.iter_mvuu_commits",
        lambda ref, enrich=False: _iter_stub(ref, enrich),
    )
    res = get_by_affected_path("b.py")
    assert len(res) == 1
    assert res[0][1].affected_files == ["b.py"]
