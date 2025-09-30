"""Tests for MVUU dashboard telemetry emission."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

import importlib.util
import sys

MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "devsynth"
    / "application"
    / "cli"
    / "commands"
    / "mvuu_dashboard_cmd.py"
)
spec = importlib.util.spec_from_file_location("mvuu_dashboard_cmd", MODULE_PATH)
mvuu_dashboard_cmd = importlib.util.module_from_spec(spec)
sys.modules.setdefault("mvuu_dashboard_cmd", mvuu_dashboard_cmd)
assert spec.loader is not None
spec.loader.exec_module(mvuu_dashboard_cmd)
from devsynth.interface.autoresearch import build_autoresearch_payload, sign_payload


@pytest.mark.fast
def test_mvuu_dashboard_cli_generates_signed_telemetry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLI should emit telemetry and pass overlay flags to Streamlit."""

    repo_root = tmp_path
    (repo_root / "src" / "devsynth" / "interface").mkdir(parents=True)
    script_path = repo_root / "src" / "devsynth" / "interface" / "mvuu_dashboard.py"
    script_path.write_text("print('stub streamlit app')\n", encoding="utf-8")

    trace_path = repo_root / "traceability.json"
    trace_payload = {
        "DSY-0001": {"utility_statement": "Investigate", "agent_persona": "Analyst"}
    }
    trace_path.write_text(json.dumps(trace_payload), encoding="utf-8")

    telemetry_path = repo_root / "telemetry.json"
    secret_env = "CLI_AUTORESEARCH_SECRET"
    monkeypatch.setenv(secret_env, "secret-value")
    monkeypatch.setenv("DEVSYNTH_REPO_ROOT", str(repo_root))

    captured = []

    def fake_run(cmd, check=False, env=None, **kwargs):
        captured.append((cmd, env))
        if cmd[:3] == ["devsynth", "mvu", "report"]:
            trace_path.write_text(json.dumps(trace_payload), encoding="utf-8")
        return type("Proc", (), {"returncode": 0})()

    monkeypatch.setattr(mvuu_dashboard_cmd.subprocess, "run", fake_run)

    exit_code = mvuu_dashboard_cmd.mvuu_dashboard_cmd(
        [
            "--research-overlays",
            "--telemetry-path",
            str(telemetry_path),
            "--signature-env",
            secret_env,
            "--research-persona",
            "Research Lead",
            "--research-persona",
            "Synthesist",
        ]
    )

    assert exit_code == 0
    assert telemetry_path.exists()

    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert "signature" in telemetry
    payload = {k: v for k, v in telemetry.items() if k != "signature"}
    signature = telemetry["signature"]
    assert signature["algorithm"] == "HMAC-SHA256"
    assert signature["key_id"] == f"env:{secret_env}"

    payload_obj = build_autoresearch_payload(
        trace_payload,
        session_id=payload["session_id"],
        generated_at=datetime.fromisoformat(payload["generated_at"]),
    )
    if "research_personas" in payload:
        payload_obj["research_personas"] = payload["research_personas"]
    expected = sign_payload(payload_obj, secret="secret-value", key_id=f"env:{secret_env}")
    assert expected.digest == signature["digest"]

    streamlit_call = next(
        (cmd, env) for cmd, env in captured if cmd[:2] == ["streamlit", "run"]
    )
    _, env = streamlit_call
    assert env["DEVSYNTH_AUTORESEARCH_OVERLAYS"] == "1"
    assert env["DEVSYNTH_AUTORESEARCH_TELEMETRY"] == str(telemetry_path)
    assert env["DEVSYNTH_AUTORESEARCH_SIGNATURE_KEY"] == secret_env
    assert env["DEVSYNTH_AUTORESEARCH_PERSONAS"] == "Research Lead,Synthesist"

    personas_payload = telemetry.get("research_personas", [])
    assert {item["name"] for item in personas_payload} == {
        "Research Lead",
        "Synthesist",
    }
    lead_payload = next(item for item in personas_payload if item["name"] == "Research Lead")
    assert lead_payload["primary_role"] == "primus"
    assert "capabilities" in lead_payload and lead_payload["capabilities"]

    monkeypatch.delenv("DEVSYNTH_REPO_ROOT", raising=False)
    monkeypatch.delenv(secret_env, raising=False)
