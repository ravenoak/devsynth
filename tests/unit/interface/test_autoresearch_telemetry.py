"""Tests for Autoresearch telemetry utilities."""

from __future__ import annotations

import pytest

from devsynth.interface.autoresearch import (
    AutoresearchPayload,
    SignatureEnvelope,
    build_autoresearch_payload,
    sign_payload,
    verify_signature,
)


def _minimal_payload() -> AutoresearchPayload:
    return {
        "version": "1.0",
        "generated_at": "2025-01-01T00:00:00+00:00",
        "session_id": "session",
        "timeline": [],
        "provenance_filters": [],
        "integrity_badges": [],
    }


@pytest.mark.fast
def test_build_autoresearch_payload_produces_timeline_snapshot() -> None:
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

    payload = build_autoresearch_payload(sample, session_id="test-session", generated_at=None)

    assert payload["version"] == "1.0"
    assert payload["session_id"] == "test-session"
    assert [event["trace_id"] for event in payload["timeline"]] == ["DSY-0001", "DSY-0002"]
    assert payload["provenance_filters"][0]["label"].startswith("Agent Persona")
    assert payload["integrity_badges"][0]["trace_id"] == "DSY-0001"


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
