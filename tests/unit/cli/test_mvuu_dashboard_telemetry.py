"""Tests for MVUU dashboard telemetry emission."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

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
from devsynth.interface.research_telemetry import sign_payload


def _prepare_cli_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    trace_payload: dict[str, object],
) -> tuple[Path, Path, list[tuple[list[str], dict[str, str] | None]]]:
    """Create a temporary repo layout and patch subprocess invocation."""

    repo_root = tmp_path
    (repo_root / "src" / "devsynth" / "interface").mkdir(parents=True)
    script_path = repo_root / "src" / "devsynth" / "interface" / "mvuu_dashboard.py"
    script_path.write_text("print('stub streamlit app')\n", encoding="utf-8")

    trace_path = repo_root / "traceability.json"
    trace_path.write_text(json.dumps(trace_payload), encoding="utf-8")

    telemetry_path = repo_root / "telemetry.json"
    monkeypatch.setenv("DEVSYNTH_REPO_ROOT", str(repo_root))

    captured: list[tuple[list[str], dict[str, str] | None]] = []

    def fake_run(cmd, check=False, env=None, **kwargs):
        captured.append((cmd, env))
        if cmd[:3] == ["devsynth", "mvu", "report"]:
            trace_path.write_text(json.dumps(trace_payload), encoding="utf-8")
        return type("Proc", (), {"returncode": 0})()

    monkeypatch.setattr(mvuu_dashboard_cmd.subprocess, "run", fake_run)

    return telemetry_path, trace_path, captured


@pytest.mark.fast
def test_mvuu_dashboard_cli_generates_signed_telemetry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLI should emit telemetry and pass overlay flags to Streamlit."""

    trace_payload = {
        "DSY-0001": {"utility_statement": "Investigate", "agent_persona": "Analyst"}
    }
    telemetry_path, trace_path, captured = _prepare_cli_environment(
        tmp_path, monkeypatch, trace_payload=trace_payload
    )
    secret_env = "CLI_EXTERNAL_RESEARCH_SECRET"
    monkeypatch.setenv(secret_env, "secret-value")

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
            "--research-persona",
            "Bibliographer",
            "--research-persona",
            "Synthesizer",
            "--research-persona",
            "Contrarian",
            "--research-persona",
            "Fact Checker",
            "--research-persona",
            "Planner",
            "--research-persona",
            "Moderator",
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

    connector_status = payload["connector_status"]
    assert connector_status["mode"] == "fixture"
    assert connector_status["provider"] == "local"
    assert connector_status["forced_local"] is False
    assert (
        "reasons" in connector_status
        and "not-configured" in connector_status["reasons"]
    )

    expected = sign_payload(payload, secret="secret-value", key_id=f"env:{secret_env}")
    assert expected.digest == signature["digest"]

    assert payload["socratic_checkpoints"] == []
    assert payload["debate_logs"] == []
    assert payload["planner_graph_exports"] == []

    streamlit_call = next(
        (cmd, env) for cmd, env in captured if cmd[:2] == ["streamlit", "run"]
    )
    _, env = streamlit_call
    assert env["DEVSYNTH_EXTERNAL_RESEARCH_OVERLAYS"] == "1"
    assert env["DEVSYNTH_EXTERNAL_RESEARCH_TELEMETRY"] == str(telemetry_path)
    assert env["DEVSYNTH_EXTERNAL_RESEARCH_SIGNATURE_KEY"] == secret_env
    assert env["DEVSYNTH_EXTERNAL_RESEARCH_MODE"] == "fixture"
    assert (
        env["DEVSYNTH_EXTERNAL_RESEARCH_PERSONAS"]
        == "Research Lead,Synthesist,Bibliographer,Synthesizer,Contrarian,Fact Checker,Planner,Moderator"
    )
    assert env["DEVSYNTH_AUTORESEARCH_OVERLAYS"] == "1"
    assert env["DEVSYNTH_AUTORESEARCH_TELEMETRY"] == str(telemetry_path)
    assert env["DEVSYNTH_AUTORESEARCH_SIGNATURE_KEY"] == secret_env
    assert (
        env["DEVSYNTH_AUTORESEARCH_PERSONAS"]
        == "Research Lead,Synthesist,Bibliographer,Synthesizer,Contrarian,Fact Checker,Planner,Moderator"
    )

    personas_payload = telemetry.get("research_personas", [])
    assert {item["name"] for item in personas_payload} == {
        "Research Lead",
        "Synthesist",
        "Bibliographer",
        "Synthesizer",
        "Contrarian",
        "Fact Checker",
        "Planner",
        "Moderator",
    }
    lead_payload = next(
        item for item in personas_payload if item["name"] == "Research Lead"
    )
    assert lead_payload["primary_role"] == "primus"
    assert "capabilities" in lead_payload and lead_payload["capabilities"]
    assert lead_payload.get("prompt_template")
    assert lead_payload.get("fallback_behavior")
    assert lead_payload.get("success_criteria")

    for persona_entry in personas_payload:
        assert persona_entry.get("prompt_template")
        assert persona_entry.get("fallback_behavior")
        assert persona_entry.get("success_criteria")

    monkeypatch.delenv("DEVSYNTH_REPO_ROOT", raising=False)
    monkeypatch.delenv(secret_env, raising=False)


@pytest.mark.fast
def test_mvuu_dashboard_cli_uses_live_connectors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When connectors are available the CLI records live mode metadata."""

    trace_payload = {
        "DSY-1001": {"utility_statement": "Correlate signals", "agent_persona": "Lead"}
    }
    telemetry_path, _trace_path, captured = _prepare_cli_environment(
        tmp_path, monkeypatch, trace_payload=trace_payload
    )
    secret_env = "CLI_EXTERNAL_RESEARCH_SECRET"
    monkeypatch.setenv(secret_env, "secret-value")
    monkeypatch.setenv("DEVSYNTH_EXTERNAL_RESEARCH_CONNECTORS", "1")

    class StubClient:
        def __init__(self) -> None:
            self.handshake_calls: list[str] = []
            self.fetch_calls: list[tuple[str, str | None]] = []

        def handshake(self, session_id: str) -> dict[str, object]:
            self.handshake_calls.append(session_id)
            return {
                "health": {"status": "ok"},
                "session": {"session_id": session_id},
                "capabilities": {"tools": ["sparql"]},
            }

        def fetch_trace_updates(
            self, sparql_query: str, session_id: str | None = None
        ) -> dict[str, object]:
            self.fetch_calls.append((sparql_query, session_id))
            return {
                "results": {
                    "records": [{"trace_id": "remote-1"}],
                    "session_id": session_id,
                },
                "metrics": {"pending": 0},
                "extended_metadata": {
                    "socratic_checkpoints": [
                        {
                            "checkpoint_id": "remote-ck",
                            "prompt": "Why now?",
                            "response": "Connector insight",
                        }
                    ],
                    "debate_logs": [
                        {
                            "label": "Remote Debate",
                            "transcript": ["Point", "Counterpoint"],
                        }
                    ],
                    "planner_graph_exports": [
                        {
                            "graph_id": "remote-graph",
                            "graphviz_source": "digraph { remote -> local }",
                        }
                    ],
                },
            }

    stub_client = StubClient()

    def fake_builder(*, enabled: bool) -> StubClient:
        assert enabled is True
        return stub_client

    monkeypatch.setattr(mvuu_dashboard_cmd, "_build_autoresearch_client", fake_builder)

    exit_code = mvuu_dashboard_cmd.mvuu_dashboard_cmd(
        [
            "--research-overlays",
            "--telemetry-path",
            str(telemetry_path),
            "--signature-env",
            secret_env,
        ]
    )

    assert exit_code == 0
    assert telemetry_path.exists()

    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    connector_status = telemetry["connector_status"]
    assert connector_status["mode"] == "live"
    assert connector_status["forced_local"] is False
    assert connector_status.get("reasons") in (None, [])
    assert (
        connector_status["handshake"]["session"]["session_id"]
        == telemetry["session_id"]
    )
    assert connector_status["query"]["results"]["records"] == [{"trace_id": "remote-1"}]
    assert telemetry["socratic_checkpoints"][0]["checkpoint_id"] == "remote-ck"
    assert telemetry["debate_logs"][0]["label"] == "Remote Debate"
    assert telemetry["planner_graph_exports"][0]["graphviz_source"].startswith(
        "digraph"
    )

    assert stub_client.handshake_calls
    assert stub_client.fetch_calls

    streamlit_call = next(
        (cmd, env) for cmd, env in captured if cmd[:2] == ["streamlit", "run"]
    )
    _, env = streamlit_call
    assert env["DEVSYNTH_EXTERNAL_RESEARCH_MODE"] == "live"

    monkeypatch.delenv("DEVSYNTH_REPO_ROOT", raising=False)
    monkeypatch.delenv(secret_env, raising=False)
    monkeypatch.delenv("DEVSYNTH_EXTERNAL_RESEARCH_CONNECTORS", raising=False)


@pytest.mark.fast
def test_mvuu_dashboard_cli_falls_back_on_connector_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Connector failures should not abort the CLI and retain fixture mode."""

    trace_payload = {"DSY-2002": {"utility_statement": "Index references"}}
    telemetry_path, _trace_path, captured = _prepare_cli_environment(
        tmp_path, monkeypatch, trace_payload=trace_payload
    )
    secret_env = "CLI_EXTERNAL_RESEARCH_SECRET"
    monkeypatch.setenv(secret_env, "secret-value")
    monkeypatch.setenv("DEVSYNTH_EXTERNAL_RESEARCH_CONNECTORS", "1")

    class RaisingClient:
        def __init__(self) -> None:
            self.handshake_calls = 0
            self.fetch_calls = 0

        def handshake(self, session_id: str) -> dict[str, object]:
            self.handshake_calls += 1
            raise RuntimeError("handshake failure")

        def fetch_trace_updates(
            self, sparql_query: str, session_id: str | None = None
        ) -> dict[str, object]:
            self.fetch_calls += 1
            return {}

    stub_client = RaisingClient()

    def fake_builder(*, enabled: bool) -> RaisingClient:
        assert enabled is True
        return stub_client

    monkeypatch.setattr(mvuu_dashboard_cmd, "_build_autoresearch_client", fake_builder)

    exit_code = mvuu_dashboard_cmd.mvuu_dashboard_cmd(
        [
            "--research-overlays",
            "--telemetry-path",
            str(telemetry_path),
            "--signature-env",
            secret_env,
        ]
    )

    assert exit_code == 0
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    connector_status = telemetry["connector_status"]
    assert connector_status["mode"] == "fixture"
    assert "handshake-error" in connector_status["reasons"]
    assert "query" not in connector_status

    assert stub_client.handshake_calls == 1
    assert stub_client.fetch_calls == 0

    streamlit_call = next(
        (cmd, env) for cmd, env in captured if cmd[:2] == ["streamlit", "run"]
    )
    _, env = streamlit_call
    assert env["DEVSYNTH_EXTERNAL_RESEARCH_MODE"] == "fixture"

    monkeypatch.delenv("DEVSYNTH_REPO_ROOT", raising=False)
    monkeypatch.delenv(secret_env, raising=False)
    monkeypatch.delenv("DEVSYNTH_EXTERNAL_RESEARCH_CONNECTORS", raising=False)


@pytest.mark.fast
def test_mvuu_dashboard_cli_force_local_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Force-local flag should bypass connector construction entirely."""

    trace_payload = {"DSY-3003": {"utility_statement": "Summarise"}}
    telemetry_path, _trace_path, captured = _prepare_cli_environment(
        tmp_path, monkeypatch, trace_payload=trace_payload
    )
    secret_env = "CLI_EXTERNAL_RESEARCH_SECRET"
    monkeypatch.setenv(secret_env, "secret-value")
    monkeypatch.setenv("DEVSYNTH_EXTERNAL_RESEARCH_CONNECTORS", "1")

    def failing_builder(*, enabled: bool):  # type: ignore[no-untyped-def]
        raise AssertionError("builder should not be called when forced local")

    monkeypatch.setattr(
        mvuu_dashboard_cmd, "_build_autoresearch_client", failing_builder
    )

    exit_code = mvuu_dashboard_cmd.mvuu_dashboard_cmd(
        [
            "--research-overlays",
            "--telemetry-path",
            str(telemetry_path),
            "--signature-env",
            secret_env,
            "--force-local-research",
        ]
    )

    assert exit_code == 0
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    connector_status = telemetry["connector_status"]
    assert connector_status["mode"] == "fixture"
    assert connector_status["forced_local"] is True
    assert "forced-local" in connector_status["reasons"]

    streamlit_call = next(
        (cmd, env) for cmd, env in captured if cmd[:2] == ["streamlit", "run"]
    )
    _, env = streamlit_call
    assert env["DEVSYNTH_EXTERNAL_RESEARCH_MODE"] == "fixture"

    monkeypatch.delenv("DEVSYNTH_REPO_ROOT", raising=False)
    monkeypatch.delenv(secret_env, raising=False)
    monkeypatch.delenv("DEVSYNTH_EXTERNAL_RESEARCH_CONNECTORS", raising=False)
