"""Tests for the MVUU dashboard interface."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from devsynth.interface import mvuu_dashboard


def test_load_traceability_reads_default_file():
    data = mvuu_dashboard.load_traceability()
    assert "DSY-0001" in data
    entry = data["DSY-0001"]
    assert entry.get("mvuu") is True


def test_load_traceability_reads_specified_file(tmp_path: Path):
    sample = {"MVUU-9999": {"mvuu": True}}
    path = tmp_path / "trace.json"
    path.write_text(json.dumps(sample), encoding="utf-8")

    data = mvuu_dashboard.load_traceability(path)
    assert data == sample


def test_render_dashboard_invokes_streamlit(monkeypatch: pytest.MonkeyPatch):
    data = {"DSY-0001": {"mvuu": True, "issue": "DSY-0001", "files": ["file.txt"], "features": []}}

    mock_sidebar = MagicMock()
    mock_sidebar.selectbox.return_value = "DSY-0001"

    mock_st = MagicMock()
    mock_st.sidebar = mock_sidebar

    monkeypatch.setattr(mvuu_dashboard, "st", mock_st)

    mvuu_dashboard.render_dashboard(data)

    mock_st.title.assert_called_once_with("MVUU Traceability Dashboard")
    mock_sidebar.header.assert_called_once_with("TraceIDs")
    mock_sidebar.selectbox.assert_called_once_with("Select TraceID", ["DSY-0001"])
    mock_st.subheader.assert_called_once_with("TraceID: DSY-0001")
    mock_st.markdown.assert_any_call("**Linked Issue:** DSY-0001")
    mock_st.markdown.assert_any_call("### Affected Files")
    mock_st.write.assert_called_once_with("file.txt")
