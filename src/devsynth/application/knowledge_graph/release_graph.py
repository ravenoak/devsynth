"""Release knowledge graph adapters.

This module implements light-weight adapters that project release readiness
artifacts into a knowledge graph representation.  The specification for the
schema lives in ``docs/specifications/knowledge-graph-release-enablers.md`` and
calls for three node types:

* :class:`ReleaseEvidenceNode` – immutable records for coverage, typing and
  similar artifacts on disk.
* :class:`TestRunNode` – metadata describing an execution of the test runner or
  typing sweep.
* :class:`QualityGateNode` – the logical gate evaluated from a run along with
  its threshold and status.

The adapters provide an in-memory NetworkX-backed graph that persists to disk
under ``.devsynth/knowledge_graph``.  When the optional ``kuzu`` dependency is
available the :class:`KuzuReleaseGraphAdapter` mirrors the NetworkX state into a
Kùzu database so rehearsals can be inspected outside of agent execution.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class ReleaseGraphError(RuntimeError):
    """Raised when persisting or loading the release knowledge graph fails."""


@dataclass(slots=True)
class ReleaseEvidenceNode:
    """Concrete representation of a release artifact."""

    id: str
    release_tag: str
    artifact_path: str
    artifact_type: str
    collected_at: str
    checksum: str
    source_command: str


@dataclass(slots=True)
class TestRunNode:
    """Metadata describing an execution of the gating commands."""

    id: str
    profile: str
    coverage_percent: float | None
    tests_collected: int | None
    exit_code: int
    started_at: str
    completed_at: str
    run_checksum: str
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class QualityGateNode:
    """Logical gate evaluated from a :class:`TestRunNode`."""

    id: str
    gate_name: str
    threshold: float
    status: str
    evaluated_at: str
    metadata: Mapping[str, object] = field(default_factory=dict)


class ReleaseGraphAdapter:
    """Protocol for adapters capable of storing release graph nodes."""

    backend_name = "abstract"

    def upsert_release_evidence(
        self, node: ReleaseEvidenceNode
    ) -> tuple[ReleaseEvidenceNode, bool]:
        raise NotImplementedError

    def upsert_test_run(
        self, node: TestRunNode
    ) -> tuple[TestRunNode, bool]:  # pragma: no cover - interface
        raise NotImplementedError

    def record_quality_gate(
        self,
        node: QualityGateNode,
        test_run_id: str,
        evidence_ids: Sequence[str],
    ) -> tuple[QualityGateNode, bool]:  # pragma: no cover - interface
        raise NotImplementedError

    def link_test_run_to_evidence(self, test_run_id: str, evidence_id: str) -> None:
        raise NotImplementedError  # pragma: no cover - interface

    def finalize(self) -> None:  # pragma: no cover - interface
        """Persist any pending state."""


class NetworkXReleaseGraphAdapter(ReleaseGraphAdapter):
    """Store release graph information in a NetworkX ``MultiDiGraph``."""

    backend_name = "networkx"

    def __init__(self, graph_path: str | Path | None = None) -> None:
        self._graph_path = Path(
            graph_path or Path(".devsynth") / "knowledge_graph" / "release_graph.json"
        )
        self._graph_path.parent.mkdir(parents=True, exist_ok=True)
        self._graph = self._load()

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _load(self) -> nx.MultiDiGraph:
        if not self._graph_path.exists():
            return nx.MultiDiGraph()
        try:
            data = json.loads(self._graph_path.read_text())
            return json_graph.node_link_graph(data, directed=True, multigraph=True)
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ReleaseGraphError(
                f"Failed to load release graph from {self._graph_path}: {exc}"
            ) from exc

    def _save(self) -> None:
        serialised = json_graph.node_link_data(self._graph)
        self._graph_path.write_text(json.dumps(serialised, indent=2))

    def _find_node(self, *, type_: str, **criteria: object) -> str | None:
        for node_id, attrs in self._graph.nodes(data=True):
            if attrs.get("type") != type_:
                continue
            if all(attrs.get(key) == value for key, value in criteria.items()):
                return str(node_id)
        return None

    def _ensure_node(
        self, node_id: str, payload: Mapping[str, object]
    ) -> tuple[str, bool]:
        created = node_id not in self._graph
        self._graph.add_node(node_id)
        nx_attrs = self._graph.nodes[node_id]
        nx_attrs.clear()
        nx_attrs.update(payload)
        return node_id, created

    # ------------------------------------------------------------------
    # adapter API
    # ------------------------------------------------------------------
    def upsert_release_evidence(
        self, node: ReleaseEvidenceNode
    ) -> tuple[ReleaseEvidenceNode, bool]:
        existing_id = self._find_node(
            type_="ReleaseEvidence",
            artifact_type=node.artifact_type,
            checksum=node.checksum,
            release_tag=node.release_tag,
        )
        node_id = existing_id or node.id or str(uuid.uuid4())
        payload = asdict(node)
        payload["id"] = node_id
        graph_payload = {**payload, "type": "ReleaseEvidence"}
        node_id, created = self._ensure_node(node_id, graph_payload)
        stored = ReleaseEvidenceNode(**payload)
        return stored, created

    def upsert_test_run(self, node: TestRunNode) -> tuple[TestRunNode, bool]:
        existing_id = self._find_node(type_="TestRun", run_checksum=node.run_checksum)
        node_id = existing_id or node.id or str(uuid.uuid4())
        payload = asdict(node)
        payload["id"] = node_id
        graph_payload = {**payload, "type": "TestRun"}
        node_id, created = self._ensure_node(node_id, graph_payload)
        stored = TestRunNode(**payload)
        return stored, created

    def link_test_run_to_evidence(self, test_run_id: str, evidence_id: str) -> None:
        existing_edges = [
            (u, v, key)
            for u, v, key, attrs in self._graph.edges(data=True, keys=True)
            if u == test_run_id and v == evidence_id and attrs.get("type") == "EMITS"
        ]
        for edge in existing_edges:
            self._graph.remove_edge(*edge)
        edge_key = f"EMITS::{test_run_id}->{evidence_id}"
        self._graph.add_edge(test_run_id, evidence_id, key=edge_key, type="EMITS")

    def record_quality_gate(
        self,
        node: QualityGateNode,
        test_run_id: str,
        evidence_ids: Sequence[str],
    ) -> tuple[QualityGateNode, bool]:
        existing_id = self._find_node(type_="QualityGate", gate_name=node.gate_name)
        node_id = existing_id or node.id or str(uuid.uuid4())
        payload = asdict(node)
        payload["id"] = node_id
        graph_payload = {**payload, "type": "QualityGate"}
        node_id, created = self._ensure_node(node_id, graph_payload)

        # Refresh relationships: HAS_EVIDENCE and EVALUATED_FROM
        for u, v, key, attrs in list(self._graph.edges(data=True, keys=True)):
            if u != node_id:
                continue
            if attrs.get("type") in {"HAS_EVIDENCE", "EVALUATED_FROM"}:
                self._graph.remove_edge(u, v, key)

        for evidence_id in evidence_ids:
            edge_key = f"HAS_EVIDENCE::{node_id}->{evidence_id}"
            self._graph.add_edge(
                node_id, evidence_id, key=edge_key, type="HAS_EVIDENCE"
            )

        eval_key = f"EVALUATED_FROM::{node_id}->{test_run_id}"
        self._graph.add_edge(node_id, test_run_id, key=eval_key, type="EVALUATED_FROM")

        stored = QualityGateNode(**payload)
        return stored, created

    def finalize(self) -> None:
        self._save()


class KuzuReleaseGraphAdapter(NetworkXReleaseGraphAdapter):
    """Persist the graph to Kùzu when the dependency is available."""

    backend_name = "kuzu"

    def __init__(
        self,
        graph_path: str | Path | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        super().__init__(graph_path=graph_path)
        self._db_path = Path(db_path or Path(".devsynth") / "knowledge_graph" / "kuzu")
        self._conn = None
        self._kuzu_available = False
        try:  # pragma: no cover - optional dependency
            import kuzu  # type: ignore

            self._db_path.mkdir(parents=True, exist_ok=True)
            database = kuzu.Database(str(self._db_path / "release_graph.db"))
            self._conn = kuzu.Connection(database)
            self._kuzu_available = True
            self._initialise_schema()
        except Exception as exc:  # pragma: no cover - graceful fallback
            logger.warning(
                "Kuzu backend unavailable for release graph ingestion: %s", exc
            )
            self._conn = None
            self._kuzu_available = False

    # ------------------------------------------------------------------
    def _initialise_schema(self) -> None:
        if not self._conn:
            return
        statements = (
            """
            CREATE TABLE IF NOT EXISTS release_evidence(
                id STRING PRIMARY KEY,
                release_tag STRING,
                artifact_path STRING,
                artifact_type STRING,
                collected_at STRING,
                checksum STRING,
                source_command STRING
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS test_run(
                id STRING PRIMARY KEY,
                profile STRING,
                coverage_percent DOUBLE,
                tests_collected INT64,
                exit_code INT32,
                started_at STRING,
                completed_at STRING,
                run_checksum STRING,
                metadata STRING
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS quality_gate(
                id STRING PRIMARY KEY,
                gate_name STRING,
                threshold DOUBLE,
                status STRING,
                evaluated_at STRING,
                metadata STRING
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS test_run_emits_evidence(
                test_run_id STRING,
                evidence_id STRING,
                PRIMARY KEY (test_run_id, evidence_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS gate_has_evidence(
                gate_id STRING,
                evidence_id STRING,
                PRIMARY KEY (gate_id, evidence_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS gate_evaluated_from(
                gate_id STRING,
                test_run_id STRING,
                PRIMARY KEY (gate_id, test_run_id)
            );
            """,
        )
        for stmt in statements:
            self._conn.execute(stmt)  # pragma: no cover - requires kuzu

    def _clear_tables(self) -> None:
        if not self._conn:
            return
        for table in (
            "release_evidence",
            "test_run",
            "quality_gate",
            "test_run_emits_evidence",
            "gate_has_evidence",
            "gate_evaluated_from",
        ):
            self._conn.execute(f"DELETE FROM {table};")  # pragma: no cover

    def _sync_to_kuzu(self) -> None:
        if not self._conn:
            return
        self._clear_tables()

        for node_id, attrs in self._graph.nodes(data=True):
            type_ = attrs.get("type")
            if type_ == "ReleaseEvidence":
                self._conn.execute(
                    "MERGE INTO release_evidence(id, release_tag, artifact_path, "
                    "artifact_type, collected_at, checksum, source_command) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?);",
                    [
                        node_id,
                        attrs.get("release_tag"),
                        attrs.get("artifact_path"),
                        attrs.get("artifact_type"),
                        attrs.get("collected_at"),
                        attrs.get("checksum"),
                        attrs.get("source_command"),
                    ],
                )
            elif type_ == "TestRun":
                metadata_json = json.dumps(attrs.get("metadata", {}))
                self._conn.execute(
                    "MERGE INTO test_run(id, profile, coverage_percent, "
                    "tests_collected, exit_code, started_at, completed_at, "
                    "run_checksum, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                    [
                        node_id,
                        attrs.get("profile"),
                        attrs.get("coverage_percent"),
                        attrs.get("tests_collected"),
                        attrs.get("exit_code"),
                        attrs.get("started_at"),
                        attrs.get("completed_at"),
                        attrs.get("run_checksum"),
                        metadata_json,
                    ],
                )
            elif type_ == "QualityGate":
                metadata_json = json.dumps(attrs.get("metadata", {}))
                self._conn.execute(
                    "MERGE INTO quality_gate(id, gate_name, threshold, status, "
                    "evaluated_at, metadata) VALUES (?, ?, ?, ?, ?, ?);",
                    [
                        node_id,
                        attrs.get("gate_name"),
                        attrs.get("threshold"),
                        attrs.get("status"),
                        attrs.get("evaluated_at"),
                        metadata_json,
                    ],
                )

        for u, v, attrs in self._graph.edges(data=True):
            type_ = attrs.get("type")
            if type_ == "EMITS":
                self._conn.execute(
                    "MERGE INTO test_run_emits_evidence(test_run_id, evidence_id) "
                    "VALUES (?, ?);",
                    [u, v],
                )
            elif type_ == "HAS_EVIDENCE":
                self._conn.execute(
                    "MERGE INTO gate_has_evidence(gate_id, evidence_id) "
                    "VALUES (?, ?);",
                    [u, v],
                )
            elif type_ == "EVALUATED_FROM":
                self._conn.execute(
                    "MERGE INTO gate_evaluated_from(gate_id, test_run_id) "
                    "VALUES (?, ?);",
                    [u, v],
                )

    def finalize(self) -> None:
        super().finalize()
        if not self._kuzu_available:
            return
        try:  # pragma: no cover - requires kuzu
            self._sync_to_kuzu()
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.error("Failed to synchronise release graph to Kuzu: %s", exc)


__all__ = [
    "ReleaseGraphError",
    "ReleaseGraphAdapter",
    "ReleaseEvidenceNode",
    "TestRunNode",
    "QualityGateNode",
    "NetworkXReleaseGraphAdapter",
    "KuzuReleaseGraphAdapter",
]
