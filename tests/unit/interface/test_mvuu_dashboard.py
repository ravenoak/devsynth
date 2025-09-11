"""Tests for the MVUU dashboard interface."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from devsynth.interface import mvuu_dashboard


@pytest.mark.fast
def test_load_traceability_reads_default_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Load default traceability report.

    ReqID: N/A"""

    sample = {"DSY-0001": {"mvuu": True}}
    path = tmp_path / "trace.json"
    path.write_text(json.dumps(sample), encoding="utf-8")
    monkeypatch.setattr(mvuu_dashboard, "_DEFAULT_TRACE_PATH", path)
    monkeypatch.setattr(mvuu_dashboard.load_traceability, "__defaults__", (path,))
    monkeypatch.setattr(mvuu_dashboard.subprocess, "run", lambda *a, **k: None)
    data = mvuu_dashboard.load_traceability()
    assert data == sample


@pytest.mark.fast
def test_load_traceability_reads_specified_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Load traceability from a specified path.

    ReqID: N/A"""

    monkeypatch.setattr(mvuu_dashboard.subprocess, "run", lambda *a, **k: None)
    sample = {"MVUU-9999": {"mvuu": True}}
    path = tmp_path / "trace.json"
    path.write_text(json.dumps(sample), encoding="utf-8")

    data = mvuu_dashboard.load_traceability(path)
    assert data == sample


@pytest.mark.fast
def test_render_dashboard_invokes_streamlit(monkeypatch: pytest.MonkeyPatch):
    """Render dashboard using injected Streamlit.

    ReqID: N/A"""

    data = {
        "DSY-0001": {
            "mvuu": True,
            "issue": "DSY-0001",
            "files": ["file.txt"],
            "features": ["feat"],
        }
    }

    mock_sidebar = MagicMock()
    mock_sidebar.selectbox.return_value = "DSY-0001"

    mock_st = MagicMock()
    mock_st.sidebar = mock_sidebar

    monkeypatch.setattr(mvuu_dashboard, "_require_streamlit", lambda: mock_st)

    mvuu_dashboard.render_dashboard(data)

    mock_st.title.assert_called_once_with("MVUU Traceability Dashboard")
    mock_sidebar.header.assert_called_once_with("TraceIDs")
    mock_sidebar.selectbox.assert_called_once_with("Select TraceID", ["DSY-0001"])
    mock_st.subheader.assert_called_once_with("TraceID: DSY-0001")
    mock_st.markdown.assert_any_call("**Linked Issue:** DSY-0001")
    mock_st.markdown.assert_any_call("### Affected Files")
    mock_st.markdown.assert_any_call("### Features")
    mock_st.write.assert_any_call("file.txt")
    mock_st.write.assert_any_call("- feat")


@pytest.mark.fast
def test_require_streamlit_raises(monkeypatch: pytest.MonkeyPatch):
    """Require Streamlit raises helpful error.

    ReqID: N/A"""

    monkeypatch.setattr(
        mvuu_dashboard.importlib,
        "import_module",
        MagicMock(side_effect=ModuleNotFoundError),
    )
    with pytest.raises(mvuu_dashboard.DevSynthError):
        mvuu_dashboard._require_streamlit()
