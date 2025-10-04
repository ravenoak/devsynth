"""Utilities for recording release evidence in the knowledge graph."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence

from devsynth.application.knowledge_graph import (
    KuzuReleaseGraphAdapter,
    NetworkXReleaseGraphAdapter,
    QualityGateNode,
    ReleaseEvidenceNode,
    ReleaseGraphAdapter,
    ReleaseGraphError,
    TestRunNode,
)
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass(slots=True)
class ArtifactInfo:
    """Metadata for a single release artifact."""

    artifact_type: str
    path: str
    checksum: str
    collected_at: str


@dataclass(slots=True)
class PublicationSummary:
    """Result of publishing a manifest to the knowledge graph."""

    test_run_id: str
    quality_gate_id: str
    evidence_ids: tuple[str, ...]
    gate_status: str
    created: Mapping[str, object]
    adapter_backend: str


@dataclass(slots=True)
class _TestRunPayload:
    profile: str
    coverage_percent: float | None
    tests_collected: int | None
    exit_code: int
    started_at: str
    completed_at: str
    run_checksum: str
    metadata: MutableMapping[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class _QualityGatePayload:
    gate_name: str
    threshold: float
    status: str
    evaluated_at: str
    metadata: MutableMapping[str, object] = field(default_factory=dict)


def compute_file_checksum(path: Path) -> str:
    """Return the SHA-256 checksum for ``path`` contents."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_release_tag(default: str = "unknown") -> str:
    """Determine the active release tag.

    The helper first honours ``DEVSYNTH_RELEASE_TAG`` for operator overrides and
    falls back to the Poetry project version recorded in ``pyproject.toml``.
    """

    tag = os.environ.get("DEVSYNTH_RELEASE_TAG")
    if tag:
        return tag
    try:
        import tomllib

        pyproject = tomllib.loads(Path("pyproject.toml").read_text())
        version = pyproject.get("tool", {}).get("poetry", {}).get("version")
        if isinstance(version, str):
            return version
    except Exception:  # pragma: no cover - defensive guard
        logger.debug("Unable to derive release tag from pyproject.toml", exc_info=True)
    return default


def create_release_graph_adapter() -> ReleaseGraphAdapter:
    """Instantiate a release graph adapter using configured backends."""

    preferred = os.environ.get("DEVSYNTH_RELEASE_GRAPH_BACKEND", "networkx")
    if preferred.lower() == "kuzu":
        try:
            return KuzuReleaseGraphAdapter()
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning(
                "Falling back to NetworkX release graph adapter: %s", exc
            )
    return NetworkXReleaseGraphAdapter()


def _build_test_run(payload: Mapping[str, Any]) -> _TestRunPayload:
    return _TestRunPayload(
        profile=str(payload.get("profile", "unknown")),
        coverage_percent=payload.get("coverage_percent"),
        tests_collected=payload.get("tests_collected"),
        exit_code=int(payload.get("exit_code", 0)),
        started_at=str(payload.get("started_at")),
        completed_at=str(payload.get("completed_at")),
        run_checksum=str(payload.get("run_checksum")),
        metadata=dict(payload.get("metadata", {})),
    )


def _build_quality_gate(payload: Mapping[str, Any]) -> _QualityGatePayload:
    return _QualityGatePayload(
        gate_name=str(payload.get("gate_name", "unknown")),
        threshold=float(payload.get("threshold", 0.0)),
        status=str(payload.get("status", "unknown")),
        evaluated_at=str(payload.get("evaluated_at")),
        metadata=dict(payload.get("metadata", {})),
    )


def publish_manifest(manifest: Mapping[str, Any]) -> PublicationSummary:
    """Publish ``manifest`` to the configured release knowledge graph."""

    adapter = create_release_graph_adapter()
    try:
        return _publish_with_adapter(adapter, manifest)
    finally:
        try:
            adapter.finalize()
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.error("Failed to persist release graph: %s", exc)


def _publish_with_adapter(
    adapter: ReleaseGraphAdapter, manifest: Mapping[str, Any]
) -> PublicationSummary:
    release_tag = str(manifest.get("release_tag", "unknown"))
    source_command = str(manifest.get("source_command", ""))
    artifacts_payload = manifest.get("artifacts")
    if not isinstance(artifacts_payload, Sequence) or not artifacts_payload:
        raise ReleaseGraphError("Manifest missing artifact definitions")

    artifacts: list[tuple[ReleaseEvidenceNode, bool]] = []
    for artifact in artifacts_payload:
        if not isinstance(artifact, Mapping):
            raise ReleaseGraphError("Artifact entry must be a mapping")
        path = Path(str(artifact.get("path")))
        node = ReleaseEvidenceNode(
            id=str(uuid.uuid4()),
            release_tag=release_tag,
            artifact_path=str(path),
            artifact_type=str(artifact.get("artifact_type")),
            collected_at=str(artifact.get("collected_at")),
            checksum=str(artifact.get("checksum")),
            source_command=source_command,
        )
        stored, created = adapter.upsert_release_evidence(node)
        artifacts.append((stored, created))

    test_run_payload = manifest.get("test_run")
    if not isinstance(test_run_payload, Mapping):
        raise ReleaseGraphError("Manifest missing test_run payload")
    test_run = _build_test_run(test_run_payload)

    test_run_node = TestRunNode(
        id=str(uuid.uuid4()),
        profile=test_run.profile,
        coverage_percent=test_run.coverage_percent,
        tests_collected=test_run.tests_collected,
        exit_code=test_run.exit_code,
        started_at=test_run.started_at,
        completed_at=test_run.completed_at,
        run_checksum=test_run.run_checksum,
        metadata=test_run.metadata,
    )
    stored_test_run, test_run_created = adapter.upsert_test_run(test_run_node)
    for evidence_node, _ in artifacts:
        adapter.link_test_run_to_evidence(stored_test_run.id, evidence_node.id)

    gate_payload = manifest.get("quality_gate")
    if not isinstance(gate_payload, Mapping):
        raise ReleaseGraphError("Manifest missing quality_gate payload")
    quality_gate = _build_quality_gate(gate_payload)
    quality_gate_node = QualityGateNode(
        id=str(uuid.uuid4()),
        gate_name=quality_gate.gate_name,
        threshold=quality_gate.threshold,
        status=quality_gate.status,
        evaluated_at=quality_gate.evaluated_at,
        metadata=quality_gate.metadata,
    )
    stored_gate, gate_created = adapter.record_quality_gate(
        quality_gate_node,
        stored_test_run.id,
        [evidence.id for evidence, _ in artifacts],
    )

    return PublicationSummary(
        test_run_id=stored_test_run.id,
        quality_gate_id=stored_gate.id,
        evidence_ids=tuple(node.id for node, _ in artifacts),
        gate_status=stored_gate.status,
        created={
            "test_run": test_run_created,
            "quality_gate": gate_created,
            "release_evidence": [created for _, created in artifacts],
        },
        adapter_backend=adapter.backend_name,
    )


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    """Write ``manifest`` to ``path`` with pretty JSON formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n")


__all__ = [
    "ArtifactInfo",
    "PublicationSummary",
    "compute_file_checksum",
    "create_release_graph_adapter",
    "get_release_tag",
    "publish_manifest",
    "write_manifest",
]

