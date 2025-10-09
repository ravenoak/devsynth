"""Utilities for external research telemetry overlays.

This module generalizes the telemetry helpers previously scoped to
Autoresearch. Autoresearch remains the upstream provider, but DevSynth now
refers to these flows generically so alternative research telemetry sources can
participate via dependency-injected connectors.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, NotRequired, TypedDict, cast
from uuid import uuid4

from devsynth.integrations import A2AConnector, MCPConnector

DEFAULT_SIGNATURE_ALGORITHM = "HMAC-SHA256"
DEFAULT_SESSION_PREFIX = "external-research"


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


class TimelineRowPayload(TypedDict):
    trace_id: str
    summary: str
    timestamp: str
    agent_persona: str
    knowledge_refs: list[str]


class ProvenanceFilterPayload(TypedDict):
    dimension: str
    label: str
    value: str


class IntegrityBadgePayload(TypedDict):
    trace_id: str
    status: str
    evidence_hash: str
    notes: str


class SocraticCheckpointPayload(TypedDict, total=False):
    checkpoint_id: NotRequired[str]
    prompt: NotRequired[str]
    response: NotRequired[str]
    rationale: NotRequired[str]
    timestamp: NotRequired[str]
    raw: NotRequired[dict[str, Any]]


class DebateLogPayload(TypedDict, total=False):
    label: NotRequired[str]
    round: NotRequired[int]
    participants: NotRequired[list[str]]
    transcript: NotRequired[list[str]]
    outcome: NotRequired[str]
    raw: NotRequired[dict[str, Any]]


class CoalitionMessagePayload(TypedDict, total=False):
    channel: NotRequired[str]
    sender: NotRequired[str]
    role: NotRequired[str]
    message: NotRequired[str]
    timestamp: NotRequired[str]
    raw: NotRequired[dict[str, Any]]


class QueryStateSnapshotPayload(TypedDict, total=False):
    name: NotRequired[str]
    status: NotRequired[str]
    summary: NotRequired[str]
    raw: NotRequired[dict[str, Any]]


class PlannerGraphExportPayload(TypedDict, total=False):
    graph_id: NotRequired[str]
    title: NotRequired[str]
    format: NotRequired[str]
    graphviz_source: NotRequired[str]
    data: NotRequired[dict[str, Any]]
    raw: NotRequired[dict[str, Any]]


class ResearchTelemetryPayload(TypedDict):
    version: str
    generated_at: str
    session_id: str
    timeline: list[TimelineRowPayload]
    provenance_filters: list[ProvenanceFilterPayload]
    integrity_badges: list[IntegrityBadgePayload]
    socratic_checkpoints: NotRequired[list[SocraticCheckpointPayload]]
    debate_logs: NotRequired[list[DebateLogPayload]]
    coalition_messages: NotRequired[list[CoalitionMessagePayload]]
    query_state_snapshots: NotRequired[list[QueryStateSnapshotPayload]]
    planner_graph_exports: NotRequired[list[PlannerGraphExportPayload]]


@dataclass(frozen=True, slots=True)
class TimelineRow:
    trace_id: str
    summary: str
    timestamp: str
    agent_persona: str
    knowledge_refs: tuple[str, ...]

    def to_payload(self) -> TimelineRowPayload:
        return {
            "trace_id": self.trace_id,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "agent_persona": self.agent_persona,
            "knowledge_refs": list(self.knowledge_refs),
        }


@dataclass(frozen=True, slots=True)
class ProvenanceFilter:
    dimension: str
    label: str
    value: str

    def to_payload(self) -> ProvenanceFilterPayload:
        return {
            "dimension": self.dimension,
            "label": self.label,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class IntegrityBadge:
    trace_id: str
    status: str
    evidence_hash: str
    notes: str

    def to_payload(self) -> IntegrityBadgePayload:
        return {
            "trace_id": self.trace_id,
            "status": self.status,
            "evidence_hash": self.evidence_hash,
            "notes": self.notes,
        }


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, (int, float, bool)):
        return str(value)
    return str(value) if value else None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        for item in value:
            text = _string_or_none(item)
            if text:
                result.append(text)
        return result
    if isinstance(value, Mapping):
        result = []
        for item in value.values():
            text = _string_or_none(item)
            if text:
                result.append(text)
        return result
    text = _string_or_none(value)
    return [text] if text else []


def _coerce_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _coerce_json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_coerce_json_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _coerce_json_object(mapping: Mapping[str, Any]) -> dict[str, Any]:
    return {str(k): _coerce_json_value(v) for k, v in mapping.items()}


def _normalize_metadata_sequence(value: Any) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        if value and all(isinstance(v, Mapping) for v in value.values()):
            return [dict(v) for v in value.values() if isinstance(v, Mapping)]
        return [dict(value)]
    if isinstance(value, (list, tuple, set)):
        result: list[Mapping[str, Any]] = []
        for item in value:
            if isinstance(item, Mapping):
                result.append(dict(item))
            else:
                result.append({"value": item})
        return result
    return [{"value": value}]


@dataclass(frozen=True, slots=True)
class SocraticCheckpoint:
    checkpoint_id: str | None
    prompt: str | None
    response: str | None
    rationale: str | None
    timestamp: str | None
    raw: dict[str, Any]

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "SocraticCheckpoint":
        checkpoint_id = _string_or_none(
            mapping.get("checkpoint_id")
            or mapping.get("id")
            or mapping.get("name")
            or mapping.get("slug")
            or mapping.get("label")
        )
        prompt = _string_or_none(
            mapping.get("question")
            or mapping.get("prompt")
            or mapping.get("socratic_question")
            or mapping.get("checkpoint")
        )
        response = _string_or_none(
            mapping.get("answer")
            or mapping.get("response")
            or mapping.get("resolution")
            or mapping.get("reply")
            or mapping.get("content")
        )
        rationale = _string_or_none(
            mapping.get("rationale")
            or mapping.get("analysis")
            or mapping.get("notes")
            or mapping.get("commentary")
        )
        timestamp = _string_or_none(mapping.get("timestamp") or mapping.get("time"))
        raw = _coerce_json_object(mapping)
        return cls(
            checkpoint_id=checkpoint_id,
            prompt=prompt,
            response=response,
            rationale=rationale,
            timestamp=timestamp,
            raw=raw,
        )

    def to_payload(self) -> SocraticCheckpointPayload:
        payload: SocraticCheckpointPayload = {"raw": self.raw}
        if self.checkpoint_id:
            payload["checkpoint_id"] = self.checkpoint_id
        if self.prompt:
            payload["prompt"] = self.prompt
        if self.response:
            payload["response"] = self.response
        if self.rationale:
            payload["rationale"] = self.rationale
        if self.timestamp:
            payload["timestamp"] = self.timestamp
        return payload


@dataclass(frozen=True, slots=True)
class DebateLog:
    label: str | None
    round: int | None
    participants: tuple[str, ...]
    transcript: tuple[str, ...]
    outcome: str | None
    raw: dict[str, Any]

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "DebateLog":
        label = _string_or_none(
            mapping.get("label")
            or mapping.get("topic")
            or mapping.get("summary")
            or mapping.get("title")
        )
        round_value = mapping.get("round") or mapping.get("turn") or mapping.get("step")
        try:
            round_int = int(round_value) if round_value is not None else None
        except (TypeError, ValueError):
            round_int = None
        participants = tuple(
            _string_list(mapping.get("participants") or mapping.get("agents"))
        )
        transcript_source = (
            mapping.get("transcript")
            or mapping.get("messages")
            or mapping.get("exchanges")
        )
        transcript = tuple(_string_list(transcript_source))
        outcome = _string_or_none(
            mapping.get("outcome") or mapping.get("result") or mapping.get("verdict")
        )
        raw = _coerce_json_object(mapping)
        return cls(
            label=label,
            round=round_int,
            participants=participants,
            transcript=transcript,
            outcome=outcome,
            raw=raw,
        )

    def to_payload(self) -> DebateLogPayload:
        payload: DebateLogPayload = {"raw": self.raw}
        if self.label:
            payload["label"] = self.label
        if self.round is not None:
            payload["round"] = self.round
        if self.participants:
            payload["participants"] = list(self.participants)
        if self.transcript:
            payload["transcript"] = list(self.transcript)
        if self.outcome:
            payload["outcome"] = self.outcome
        return payload


@dataclass(frozen=True, slots=True)
class CoalitionMessage:
    channel: str | None
    sender: str | None
    role: str | None
    message: str | None
    timestamp: str | None
    raw: dict[str, Any]

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "CoalitionMessage":
        channel = _string_or_none(mapping.get("channel") or mapping.get("thread"))
        sender = _string_or_none(
            mapping.get("sender") or mapping.get("author") or mapping.get("agent")
        )
        role = _string_or_none(mapping.get("role") or mapping.get("persona"))
        message = _string_or_none(
            mapping.get("message") or mapping.get("content") or mapping.get("text")
        )
        timestamp = _string_or_none(mapping.get("timestamp") or mapping.get("time"))
        raw = _coerce_json_object(mapping)
        return cls(
            channel=channel,
            sender=sender,
            role=role,
            message=message,
            timestamp=timestamp,
            raw=raw,
        )

    def to_payload(self) -> CoalitionMessagePayload:
        payload: CoalitionMessagePayload = {"raw": self.raw}
        if self.channel:
            payload["channel"] = self.channel
        if self.sender:
            payload["sender"] = self.sender
        if self.role:
            payload["role"] = self.role
        if self.message:
            payload["message"] = self.message
        if self.timestamp:
            payload["timestamp"] = self.timestamp
        return payload


@dataclass(frozen=True, slots=True)
class QueryStateSnapshot:
    name: str | None
    status: str | None
    summary: str | None
    raw: dict[str, Any]

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "QueryStateSnapshot":
        name = _string_or_none(
            mapping.get("name") or mapping.get("query") or mapping.get("identifier")
        )
        status = _string_or_none(mapping.get("status") or mapping.get("state"))
        summary = _string_or_none(
            mapping.get("summary")
            or mapping.get("description")
            or mapping.get("details")
        )
        raw = _coerce_json_object(mapping)
        return cls(name=name, status=status, summary=summary, raw=raw)

    def to_payload(self) -> QueryStateSnapshotPayload:
        payload: QueryStateSnapshotPayload = {"raw": self.raw}
        if self.name:
            payload["name"] = self.name
        if self.status:
            payload["status"] = self.status
        if self.summary:
            payload["summary"] = self.summary
        return payload


@dataclass(frozen=True, slots=True)
class PlannerGraphExport:
    graph_id: str | None
    title: str | None
    format: str | None
    graphviz_source: str | None
    data: dict[str, Any] | None
    raw: dict[str, Any]

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "PlannerGraphExport":
        graph_id = _string_or_none(
            mapping.get("graph_id") or mapping.get("id") or mapping.get("name")
        )
        title = _string_or_none(
            mapping.get("title") or mapping.get("label") or mapping.get("summary")
        )
        format_hint = _string_or_none(mapping.get("format") or mapping.get("type"))
        graphviz_source = _string_or_none(
            mapping.get("graphviz")
            or mapping.get("dot")
            or mapping.get("graphviz_source")
            or mapping.get("source")
        )
        data_candidate = (
            mapping.get("data") or mapping.get("graph") or mapping.get("content")
        )
        data: dict[str, Any] | None = None
        if isinstance(data_candidate, Mapping):
            data = _coerce_json_object(data_candidate)
        raw = _coerce_json_object(mapping)
        return cls(
            graph_id=graph_id,
            title=title,
            format=format_hint,
            graphviz_source=graphviz_source,
            data=data,
            raw=raw,
        )

    def to_payload(self) -> PlannerGraphExportPayload:
        payload: PlannerGraphExportPayload = {"raw": self.raw}
        if self.graph_id:
            payload["graph_id"] = self.graph_id
        if self.title:
            payload["title"] = self.title
        if self.format:
            payload["format"] = self.format
        if self.graphviz_source:
            payload["graphviz_source"] = self.graphviz_source
        if self.data is not None:
            payload["data"] = self.data
        return payload


@dataclass(frozen=True, slots=True)
class ExtendedMetadata:
    socratic_checkpoints: tuple[SocraticCheckpoint, ...] = ()
    debate_logs: tuple[DebateLog, ...] = ()
    coalition_messages: tuple[CoalitionMessage, ...] = ()
    query_state_snapshots: tuple[QueryStateSnapshot, ...] = ()
    planner_graph_exports: tuple[PlannerGraphExport, ...] = ()

    def merge(self, other: "ExtendedMetadata") -> "ExtendedMetadata":
        return ExtendedMetadata(
            socratic_checkpoints=self.socratic_checkpoints + other.socratic_checkpoints,
            debate_logs=self.debate_logs + other.debate_logs,
            coalition_messages=self.coalition_messages + other.coalition_messages,
            query_state_snapshots=self.query_state_snapshots
            + other.query_state_snapshots,
            planner_graph_exports=self.planner_graph_exports
            + other.planner_graph_exports,
        )

    def to_payload(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "socratic_checkpoints": [
                item.to_payload() for item in self.socratic_checkpoints
            ],
            "debate_logs": [item.to_payload() for item in self.debate_logs],
            "coalition_messages": [
                item.to_payload() for item in self.coalition_messages
            ],
            "query_state_snapshots": [
                item.to_payload() for item in self.query_state_snapshots
            ],
            "planner_graph_exports": [
                item.to_payload() for item in self.planner_graph_exports
            ],
        }


def _extract_section(
    mapping: Mapping[str, Any], keys: tuple[str, ...]
) -> list[Mapping[str, Any]]:
    for key in keys:
        if key in mapping:
            return _normalize_metadata_sequence(mapping.get(key))
    return []


def _coerce_single_source(mapping: Mapping[str, Any]) -> ExtendedMetadata:
    checkpoints = [
        SocraticCheckpoint.from_mapping(item)
        for item in _extract_section(
            mapping,
            (
                "socratic_checkpoints",
                "socratic",
                "socratic_log",
                "socratic_checklist",
                "checkpoints",
            ),
        )
    ]
    debates = [
        DebateLog.from_mapping(item)
        for item in _extract_section(
            mapping,
            ("debate_logs", "debates", "dialectic_logs", "debate", "debate_rounds"),
        )
    ]
    coalition = [
        CoalitionMessage.from_mapping(item)
        for item in _extract_section(
            mapping,
            (
                "coalition_messages",
                "coalitions",
                "coalition_log",
                "coalition",
                "team_messages",
            ),
        )
    ]
    query_states = [
        QueryStateSnapshot.from_mapping(item)
        for item in _extract_section(
            mapping,
            (
                "query_state_snapshots",
                "query_states",
                "querystate_snapshots",
                "query_logs",
                "queries",
            ),
        )
    ]
    graphs = [
        PlannerGraphExport.from_mapping(item)
        for item in _extract_section(
            mapping,
            (
                "planner_graph_exports",
                "planner_graphs",
                "graph_exports",
                "planning_graphs",
                "graphs",
            ),
        )
    ]

    sections_field = mapping.get("sections")
    if isinstance(sections_field, (list, tuple)):
        for section in sections_field:
            if not isinstance(section, Mapping):
                continue
            section_type = str(section.get("type", "")).lower()
            content = (
                section.get("content") or section.get("entries") or section.get("data")
            )
            additional = _normalize_metadata_sequence(content)
            if section_type in {"socratic", "checkpoint"}:
                checkpoints.extend(
                    SocraticCheckpoint.from_mapping(item) for item in additional
                )
            elif section_type in {"debate", "dialectic"}:
                debates.extend(DebateLog.from_mapping(item) for item in additional)
            elif section_type in {"coalition", "team"}:
                coalition.extend(
                    CoalitionMessage.from_mapping(item) for item in additional
                )
            elif section_type in {"querystate", "query", "state"}:
                query_states.extend(
                    QueryStateSnapshot.from_mapping(item) for item in additional
                )
            elif section_type in {"planner", "graph", "planning"}:
                graphs.extend(
                    PlannerGraphExport.from_mapping(item) for item in additional
                )

    return ExtendedMetadata(
        socratic_checkpoints=tuple(checkpoints),
        debate_logs=tuple(debates),
        coalition_messages=tuple(coalition),
        query_state_snapshots=tuple(query_states),
        planner_graph_exports=tuple(graphs),
    )


def _coerce_extended_metadata(metadata: Mapping[str, Any]) -> ExtendedMetadata:
    sources: list[Mapping[str, Any]] = [metadata]
    for key in ("extended_metadata", "metadata", "autoresearch"):
        nested = metadata.get(key)
        if isinstance(nested, Mapping):
            sources.append(nested)
    combined = ExtendedMetadata()
    for source in sources:
        combined = combined.merge(_coerce_single_source(source))
    return combined


def merge_extended_metadata_into_payload(
    payload: ResearchTelemetryPayload,
    extended_metadata: Mapping[str, Any] | None,
) -> ResearchTelemetryPayload:
    enriched: dict[str, Any] = {**payload}

    for field in (
        "socratic_checkpoints",
        "debate_logs",
        "coalition_messages",
        "query_state_snapshots",
        "planner_graph_exports",
    ):
        enriched.setdefault(field, [])

    if not extended_metadata:
        return cast(ResearchTelemetryPayload, enriched)

    metadata = _coerce_extended_metadata(extended_metadata)
    payload_sections = metadata.to_payload()

    for key, items in payload_sections.items():
        existing = list(enriched.get(key, []))
        existing.extend(items)
        enriched[key] = existing

    return cast(ResearchTelemetryPayload, enriched)


def _canonicalize_payload(payload: Mapping[str, Any]) -> bytes:
    """Return a canonical JSON representation for signing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _derive_session_id() -> str:
    """Generate a deterministic-looking session identifier."""

    return f"{DEFAULT_SESSION_PREFIX}-{uuid4()}"


def build_research_telemetry_payload(
    traceability: Mapping[str, Any],
    *,
    generated_at: datetime | None = None,
    session_id: str | None = None,
    mcp_connector: MCPConnector | None = None,
    a2a_connector: A2AConnector | None = None,
    extended_metadata: Mapping[str, Any] | None = None,
) -> ResearchTelemetryPayload:
    """Create the overlay payload that Streamlit will consume."""

    timestamp = (generated_at or datetime.now(timezone.utc)).isoformat()
    session = session_id or _derive_session_id()

    if mcp_connector is not None:
        mcp_connector.ensure_session(session)
    if a2a_connector is not None:
        a2a_connector.prepare_channel(session)

    metadata_keys = {
        "extended_metadata",
        "external_metadata",
        "metadata",
    }
    metadata_sources: list[Mapping[str, Any]] = []
    for key in metadata_keys:
        value = traceability.get(key)
        if isinstance(value, Mapping):
            metadata_sources.append(value)

    timeline_rows: list[TimelineRow] = []
    provenance_filters: dict[str, set[str]] = {
        "agent_persona": set(),
        "knowledge_graph": set(),
    }
    integrity_badges: list[IntegrityBadge] = []

    for trace_id, entry in traceability.items():
        if trace_id in metadata_keys and isinstance(entry, Mapping):
            continue
        entry = entry or {}
        persona = (
            entry.get("agent_persona") or entry.get("persona") or "General Researcher"
        )
        knowledge_refs = (
            entry.get("knowledge_graph_refs") or entry.get("references") or []
        )
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

        normalized_refs = [str(ref) for ref in knowledge_refs]

        timeline_rows.append(
            TimelineRow(
                trace_id=trace_id,
                summary=summary,
                timestamp=event_time,
                agent_persona=persona,
                knowledge_refs=tuple(normalized_refs),
            )
        )

        provenance_filters["agent_persona"].add(persona)
        for ref in normalized_refs:
            provenance_filters["knowledge_graph"].add(str(ref))

        badge_basis = json.dumps(
            {"trace_id": trace_id, "entry": entry}, sort_keys=True
        ).encode("utf-8")
        badge_hash = hashlib.sha256(badge_basis).hexdigest()
        integrity_badges.append(
            IntegrityBadge(
                trace_id=trace_id,
                status=entry.get(
                    "integrity_status", "verified" if badge_hash else "unknown"
                ),
                evidence_hash=badge_hash,
                notes=(
                    entry.get("integrity_notes")
                    or "Signature derived from MVUU report payload."
                ),
            )
        )

    filters_payload = [
        ProvenanceFilter(
            dimension="agent_persona",
            label=f"Agent Persona: {value}",
            value=value,
        )
        for value in sorted(provenance_filters["agent_persona"])
    ] + [
        ProvenanceFilter(
            dimension="knowledge_graph",
            label=f"Knowledge Graph: {value}",
            value=value,
        )
        for value in sorted(provenance_filters["knowledge_graph"])
    ]

    payload: ResearchTelemetryPayload = {
        "version": "1.0",
        "generated_at": timestamp,
        "session_id": session,
        "timeline": [
            row.to_payload()
            for row in sorted(timeline_rows, key=lambda item: item.timestamp)
        ],
        "provenance_filters": [filter_.to_payload() for filter_ in filters_payload],
        "integrity_badges": [badge.to_payload() for badge in integrity_badges],
    }
    enriched = merge_extended_metadata_into_payload(payload, None)
    all_metadata = list(metadata_sources)
    if extended_metadata:
        all_metadata.append(extended_metadata)
    for metadata in all_metadata:
        enriched = merge_extended_metadata_into_payload(enriched, metadata)

    return enriched


def sign_payload(
    payload: ResearchTelemetryPayload,
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


__all__ = [
    "ResearchTelemetryPayload",
    "SignatureEnvelope",
    "TimelineRow",
    "ProvenanceFilter",
    "IntegrityBadge",
    "SocraticCheckpoint",
    "DebateLog",
    "CoalitionMessage",
    "QueryStateSnapshot",
    "PlannerGraphExport",
    "merge_extended_metadata_into_payload",
    "build_research_telemetry_payload",
    "sign_payload",
    "verify_signature",
]
