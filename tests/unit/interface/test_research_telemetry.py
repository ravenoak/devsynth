"""Tests for Autoresearch telemetry utilities."""

from __future__ import annotations

import pytest

from devsynth.interface.research_telemetry import (
    ResearchTelemetryPayload,
    SignatureEnvelope,
    build_research_telemetry_payload,
    merge_extended_metadata_into_payload,
    sign_payload,
    verify_signature,
)


def _minimal_payload() -> ResearchTelemetryPayload:
    return {
        "version": "1.0",
        "generated_at": "2025-01-01T00:00:00+00:00",
        "session_id": "session",
        "timeline": [],
        "provenance_filters": [],
        "integrity_badges": [],
        "socratic_checkpoints": [],
        "debate_logs": [],
        "coalition_messages": [],
        "query_state_snapshots": [],
        "planner_graph_exports": [],
    }


class _RecordingMCPConnector:
    def __init__(self) -> None:
        self.sessions: list[str] = []

    def ensure_session(self, session_id: str) -> None:
        self.sessions.append(session_id)

    def close(self) -> None:
        pass


class _RecordingA2AConnector:
    def __init__(self) -> None:
        self.sessions: list[str] = []

    def prepare_channel(self, session_id: str) -> None:
        self.sessions.append(session_id)

    def close(self) -> None:
        pass


@pytest.mark.fast
def test_build_research_telemetry_payload_produces_timeline_snapshot() -> None:
    """Ensure payload captures timeline, filters, and badges."""

    sample = {
        "DSY-0001": {
            "utility_statement": "Investigate retrieval drift",
            "timestamp": "2024-12-01T10:00:00+00:00",
            "agent_persona": "Research Analyst",
            "knowledge_graph_refs": ["KG-42"],
        },
        "DSY-0002": {
            "summary": "Cross-check citations",
            "references": ["DOI:10.1000/xyz"],
        },
    }

    payload = build_research_telemetry_payload(
        sample,
        session_id="test-session",
        generated_at=None,
        mcp_connector=_RecordingMCPConnector(),
        a2a_connector=_RecordingA2AConnector(),
    )

    assert payload["version"] == "1.0"
    assert payload["session_id"] == "test-session"
    assert [event["trace_id"] for event in payload["timeline"]] == [
        "DSY-0001",
        "DSY-0002",
    ]
    assert payload["provenance_filters"][0]["label"].startswith("Agent Persona")
    assert payload["integrity_badges"][0]["trace_id"] == "DSY-0001"
    assert payload["socratic_checkpoints"] == []
    assert payload["planner_graph_exports"] == []


@pytest.mark.fast
def test_build_research_telemetry_payload_merges_extended_metadata() -> None:
    sample = {"DSY-0001": {"summary": "Initial"}}
    extended = {
        "socratic_checkpoints": [
            {
                "checkpoint_id": "chk-1",
                "prompt": "What is the objective?",
                "response": "Validate telemetry",
            }
        ],
        "debate_logs": [
            {
                "label": "Feasibility",
                "participants": ["Analyst", "Reviewer"],
                "transcript": ["Pros", "Cons"],
                "outcome": "Proceed",
            }
        ],
        "coalition_messages": [
            {"sender": "Coalition", "message": "Sync update", "timestamp": "2025-01-01"}
        ],
        "query_state_snapshots": [
            {"name": "Primary", "status": "ready", "summary": "Up to date"}
        ],
        "planner_graph_exports": [
            {"graph_id": "graph-1", "graphviz_source": "digraph { a -> b }"}
        ],
    }

    payload = build_research_telemetry_payload(sample, extended_metadata=extended)

    assert payload["socratic_checkpoints"][0]["checkpoint_id"] == "chk-1"
    assert payload["debate_logs"][0]["label"] == "Feasibility"
    assert payload["coalition_messages"][0]["message"] == "Sync update"
    assert payload["query_state_snapshots"][0]["name"] == "Primary"
    assert payload["planner_graph_exports"][0]["graphviz_source"].startswith("digraph")


@pytest.mark.fast
def test_merge_extended_metadata_into_payload_appends_sections() -> None:
    sample = {"DSY-0001": {"summary": "Entry"}}
    payload = build_research_telemetry_payload(sample)
    enriched = merge_extended_metadata_into_payload(
        payload,
        {"debate_logs": [{"label": "Review", "transcript": ["Check"]}]},
    )

    assert payload["debate_logs"] == []
    assert enriched is not payload
    assert enriched["debate_logs"][0]["label"] == "Review"


@pytest.mark.fast
def test_build_research_telemetry_payload_invokes_connectors() -> None:
    sample = {"DSY-0001": {}}
    mcp = _RecordingMCPConnector()
    a2a = _RecordingA2AConnector()

    build_research_telemetry_payload(
        sample,
        session_id="session-123",
        mcp_connector=mcp,
        a2a_connector=a2a,
    )

    assert mcp.sessions == ["session-123"]
    assert a2a.sessions == ["session-123"]


@pytest.mark.fast
def test_signature_roundtrip_validates() -> None:
    """Signatures should verify against canonical payloads."""

    payload = _minimal_payload()
    payload["timeline"].append(
        {
            "trace_id": "DSY-0001",
            "summary": "",
            "timestamp": "2025-01-01T00:00:00+00:00",
            "agent_persona": "Analyst",
            "knowledge_refs": [],
        }
    )
    secret = "topsecret"

    envelope = sign_payload(payload, secret=secret, key_id="env:TEST")

    assert isinstance(envelope, SignatureEnvelope)
    assert verify_signature(payload, secret=secret, signature=envelope)


@pytest.mark.fast
def test_signature_failure_with_wrong_secret() -> None:
    """Changing the secret should invalidate the signature."""

    payload = _minimal_payload()
    secret = "alpha"
    envelope = sign_payload(payload, secret=secret, key_id="env:TEST")

    assert not verify_signature(payload, secret="beta", signature=envelope)
