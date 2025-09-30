"""Utilities for Autoresearch telemetry and overlays."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

DEFAULT_SIGNATURE_ALGORITHM = "HMAC-SHA256"
DEFAULT_SESSION_PREFIX = "autoresearch"


@dataclass(frozen=True, slots=True)
class SignatureEnvelope:
    """Metadata describing a telemetry signature."""

    algorithm: str
    key_id: str
    digest: str

    def as_dict(self) -> dict[str, str]:
        return {
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "digest": self.digest,
        }


def _canonicalize_payload(payload: Mapping[str, Any]) -> bytes:
    """Return a canonical JSON representation for signing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _derive_session_id() -> str:
    """Generate a deterministic-looking session identifier."""

    return f"{DEFAULT_SESSION_PREFIX}-{uuid4()}"


def build_autoresearch_payload(
    traceability: Mapping[str, Any],
    *,
    generated_at: datetime | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Create the overlay payload that Streamlit will consume."""

    timestamp = (generated_at or datetime.now(timezone.utc)).isoformat()
    session = session_id or _derive_session_id()

    timeline: list[dict[str, Any]] = []
    provenance_filters: dict[str, set[str]] = {
        "agent_persona": set(),
        "knowledge_graph": set(),
    }
    integrity_badges: list[dict[str, Any]] = []

    for trace_id, entry in traceability.items():
        entry = entry or {}
        persona = entry.get("agent_persona") or entry.get("persona") or "General Researcher"
        knowledge_refs = entry.get("knowledge_graph_refs") or entry.get("references") or []
        if isinstance(knowledge_refs, dict):
            knowledge_refs = list(knowledge_refs.values())
        if not isinstance(knowledge_refs, list):  # pragma: no cover - guard
            knowledge_refs = [str(knowledge_refs)]

        summary = (
            entry.get("utility_statement")
            or entry.get("summary")
            or entry.get("title")
            or "Autoresearch update recorded"
        )
        event_time = entry.get("timestamp") or timestamp

        timeline.append(
            {
                "trace_id": trace_id,
                "summary": summary,
                "timestamp": event_time,
                "agent_persona": persona,
                "knowledge_refs": knowledge_refs,
            }
        )

        provenance_filters["agent_persona"].add(persona)
        for ref in knowledge_refs:
            provenance_filters["knowledge_graph"].add(str(ref))

        badge_basis = json.dumps({"trace_id": trace_id, "entry": entry}, sort_keys=True).encode("utf-8")
        badge_hash = hashlib.sha256(badge_basis).hexdigest()
        integrity_badges.append(
            {
                "trace_id": trace_id,
                "status": entry.get("integrity_status", "verified" if badge_hash else "unknown"),
                "evidence_hash": badge_hash,
                "notes": entry.get("integrity_notes") or "Signature derived from MVUU report payload.",
            }
        )

    filters_payload = [
        {
            "dimension": "agent_persona",
            "label": f"Agent Persona: {value}",
            "value": value,
        }
        for value in sorted(provenance_filters["agent_persona"])
    ] + [
        {
            "dimension": "knowledge_graph",
            "label": f"Knowledge Graph: {value}",
            "value": value,
        }
        for value in sorted(provenance_filters["knowledge_graph"])
    ]

    payload = {
        "version": "1.0",
        "generated_at": timestamp,
        "session_id": session,
        "timeline": sorted(timeline, key=lambda item: item["timestamp"]),
        "provenance_filters": filters_payload,
        "integrity_badges": integrity_badges,
    }

    return payload


def sign_payload(
    payload: Mapping[str, Any],
    *,
    secret: str,
    key_id: str,
    algorithm: str = DEFAULT_SIGNATURE_ALGORITHM,
) -> SignatureEnvelope:
    """Sign the provided payload using the shared secret."""

    canonical = _canonicalize_payload(payload)
    digest = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    return SignatureEnvelope(algorithm=algorithm, key_id=key_id, digest=digest)


def verify_signature(
    payload: Mapping[str, Any],
    *,
    secret: str,
    signature: Mapping[str, Any] | SignatureEnvelope,
) -> bool:
    """Verify a telemetry signature in constant time."""

    if not secret:
        return False

    if isinstance(signature, SignatureEnvelope):
        digest = signature.digest
        key_id = signature.key_id
    else:
        digest = str(signature.get("digest", ""))
        key_id = str(signature.get("key_id", ""))

    expected = sign_payload(payload, secret=secret, key_id=key_id).digest
    return hmac.compare_digest(expected, digest)
