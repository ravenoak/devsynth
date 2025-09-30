"""Tests for the MVUU dashboard interface."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from devsynth.interface import mvuu_dashboard
from devsynth.interface.autoresearch import build_autoresearch_payload, sign_payload


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


@pytest.mark.fast
def test_render_autoresearch_overlays_snapshot() -> None:
    """Snapshot expected overlay rendering calls."""

    telemetry = {
        "provenance_filters": [
            {"label": "Agent Persona: Analyst", "value": "Analyst", "dimension": "agent_persona"},
            {"label": "Knowledge Graph: KG-42", "value": "KG-42", "dimension": "knowledge_graph"},
        ],
        "timeline": [
            {
                "trace_id": "DSY-0001",
                "summary": "Investigate drift",
                "timestamp": "2024-01-01T00:00:00+00:00",
                "agent_persona": "Analyst",
                "knowledge_refs": ["KG-42"],
            }
        ],
        "integrity_badges": [
            {
                "trace_id": "DSY-0001",
                "status": "verified",
                "notes": "Hash matches",
                "evidence_hash": "abc123",
            }
        ],
    }

    mock_sidebar = MagicMock()
    mock_st = MagicMock()
    mock_st.sidebar = mock_sidebar
    mock_st.info = MagicMock()
    mock_st.caption = MagicMock()

    mvuu_dashboard.render_autoresearch_overlays(
        mock_st,
        telemetry,
        signature_verified=True,
        signature_error=None,
    )

    sidebar_calls = [call.args for call in mock_sidebar.multiselect.call_args_list]
    assert sidebar_calls == [
        (
            "Provenance filters",
            ["Agent Persona: Analyst", "Knowledge Graph: KG-42"],
        ),
    ]
    timeline_calls = [call.args[0] for call in mock_st.markdown.call_args_list]
    assert "### Autoresearch Timeline" in timeline_calls[0]
    assert any("DSY-0001" in call for call in timeline_calls)
    badge_line = timeline_calls[-1]
    assert "Hash matches" in badge_line


@pytest.mark.fast
def test_render_dashboard_with_overlays_loads_telemetry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dashboards should render overlays when the flag is present."""

    data = {
        "DSY-0001": {
            "issue": "DSY-0001",
            "files": [],
        }
    }

    payload = build_autoresearch_payload(
        {"DSY-0001": {"utility_statement": "Investigate"}},
        session_id="session",
    )
    secret_env = "TEST_AUTORESEARCH_SECRET"
    signature = sign_payload(payload, secret="secret", key_id=f"env:{secret_env}").as_dict()
    telemetry = payload | {"signature": signature}

    captured: dict[str, object] = {}

    def fake_render(st, telemetry_payload, *, signature_verified, signature_error):
        captured["signature_verified"] = signature_verified
        captured["signature_error"] = signature_error
        captured["payload"] = telemetry_payload

    mock_sidebar = MagicMock()
    mock_sidebar.selectbox.return_value = "DSY-0001"
    mock_st = MagicMock()
    mock_st.sidebar = mock_sidebar

    monkeypatch.setenv("DEVSYNTH_AUTORESEARCH_OVERLAYS", "1")
    monkeypatch.setenv(mvuu_dashboard._SIGNATURE_POINTER_ENV, secret_env)
    monkeypatch.setenv(secret_env, "secret")
    monkeypatch.setattr(mvuu_dashboard, "_require_streamlit", lambda: mock_st)
    monkeypatch.setattr(mvuu_dashboard, "load_autoresearch_telemetry", lambda path=None: telemetry)
    monkeypatch.setattr(mvuu_dashboard, "render_autoresearch_overlays", fake_render)

    mvuu_dashboard.render_dashboard(data)

    assert captured["signature_verified"] is True
    assert captured["signature_error"] is None
    assert captured["payload"]["session_id"] == "session"

    monkeypatch.delenv("DEVSYNTH_AUTORESEARCH_OVERLAYS", raising=False)
    monkeypatch.delenv(secret_env, raising=False)
