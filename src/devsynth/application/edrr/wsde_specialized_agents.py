"""Specialised WSDE agents that collaborate via dialectical critique loops."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any
from collections.abc import Iterable

from devsynth.application.agents.base import BaseAgent
from devsynth.application.memory.adapters.enhanced_graph_memory_adapter import (
    DEVSYNTH,
    EnhancedGraphMemoryAdapter,
)
from devsynth.logging_setup import DevSynthLogger

try:  # pragma: no cover - optional dependency in constrained environments
    from rdflib import URIRef
    from rdflib.namespace import RDFS
except Exception:  # pragma: no cover - rdflib not installed
    URIRef = None  # type: ignore[assignment]
    RDFS = None  # type: ignore[assignment]


@dataclass(slots=True)
class DialecticalExchange:
    """Structured record of a dialectical critique."""

    role: str
    claim: str
    question: str
    verdict: str
    evidence: tuple[str, ...] = ()


class DialecticalLoopMixin:
    """Mixin that captures dialectical exchanges for later inspection."""

    def __init__(self) -> None:
        self._dialectic_log: list[DialecticalExchange] = []

    def _reset_dialectic(self) -> None:
        self._dialectic_log.clear()

    def _record_exchange(
        self,
        *,
        role: str,
        claim: str,
        question: str,
        verdict: str,
        evidence: Iterable[str] | None = None,
    ) -> None:
        entry = DialecticalExchange(
            role=role,
            claim=claim,
            question=question,
            verdict=verdict,
            evidence=tuple(evidence or ()),
        )
        self._dialectic_log.append(entry)

    def get_dialectic_log(self) -> tuple[DialecticalExchange, ...]:
        """Return immutable view of the dialectical history."""

        return tuple(self._dialectic_log)


class BaseWSDESpecialist(BaseAgent, DialecticalLoopMixin):
    """Base class for WSDE specialists that rely on the enhanced graph."""

    def __init__(self) -> None:
        BaseAgent.__init__(self)
        DialecticalLoopMixin.__init__(self)
        self.logger = DevSynthLogger(self.__class__.__name__)

    def _require_graph_adapter(
        self, inputs: Mapping[str, object]
    ) -> EnhancedGraphMemoryAdapter:
        graph = inputs.get("graph_adapter")
        if not isinstance(graph, EnhancedGraphMemoryAdapter):
            raise ValueError("graph_adapter must be an EnhancedGraphMemoryAdapter")
        return graph

    def _collect_provenance(
        self,
        graph: EnhancedGraphMemoryAdapter,
        artifact_ids: Iterable[str],
    ) -> list[dict[str, object]]:
        provenance: list[dict[str, object]] = []
        graph_store = getattr(graph, "graph", None)
        if graph_store is None:
            return provenance

        for artifact_id in sorted(set(artifact_ids)):
            resolver = getattr(graph, "_resolve_node_uri", None)
            to_identifier = getattr(graph, "_uri_to_identifier", None)
            if resolver is None or to_identifier is None:
                continue
            artifact_uri = resolver(artifact_id)
            if artifact_uri is None:
                continue

            supports = self._gather_links(
                graph_store, artifact_uri, to_identifier, DEVSYNTH.supports
            )
            derived = self._gather_links(
                graph_store, artifact_uri, to_identifier, DEVSYNTH.derivedFrom
            )
            roles = self._gather_roles(graph_store, artifact_uri, to_identifier)
            provenance.append(
                {
                    "artifact": artifact_id,
                    "supports": supports,
                    "derived_from": derived,
                    "roles": roles,
                }
            )
        return provenance

    def _gather_links(
        self,
        graph_store: Any,
        subject: Any,
        to_identifier: Any,
        predicate: Any,
    ) -> tuple[str, ...]:
        values: set[str] = set()
        for _, _, obj in graph_store.triples((subject, predicate, None)):
            identifier = to_identifier(obj)
            if identifier:
                values.add(str(identifier))
        return tuple(sorted(values))

    def _gather_roles(
        self,
        graph_store: Any,
        subject: Any,
        to_identifier: Any,
    ) -> tuple[str, ...]:
        labels: set[str] = set()
        if URIRef is None:
            return tuple()
        for _, _, role_uri in graph_store.triples((subject, DEVSYNTH.hasRole, None)):
            label_value = None
            if RDFS is not None:
                label_value = graph_store.value(role_uri, RDFS.label)
            if label_value:
                labels.add(str(label_value))
                continue
            identifier = to_identifier(role_uri)
            if identifier:
                labels.add(str(identifier))
        return tuple(sorted(labels))


class ResearchLeadAgent(BaseWSDESpecialist):
    """Coordinates research planning using Socratic prompts and traversal."""

    def process(self, inputs: Mapping[str, object]) -> dict[str, object]:
        self._reset_dialectic()
        graph = self._require_graph_adapter(inputs)

        task = inputs.get("task")
        question = ""
        if isinstance(task, Mapping):
            question = str(task.get("question") or task.get("title") or "").strip()
        if not question:
            question = str(inputs.get("question") or "").strip()
        if not question:
            raise ValueError(
                "ResearchLeadAgent requires a task question for Socratic planning"
            )

        start_node = str(inputs.get("start_node") or "").strip()
        reachable: set[str] = set()
        research_nodes: set[str] = set()
        if start_node:
            reachable = graph.traverse_graph(
                start_node, max_depth=2, include_research=True
            )
            research_nodes = {
                node for node in reachable if node.startswith("artifact_")
            }
        provenance = self._collect_provenance(graph, research_nodes)
        verdict = "accepted" if provenance else "needs-evidence"
        self._record_exchange(
            role="Research Lead",
            claim=question,
            question="What graph evidence supports this investigation?",
            verdict=verdict,
            evidence=(sorted(research_nodes) if research_nodes else ()),
        )

        plan = {
            "question": question,
            "start_node": start_node,
            "reachable_nodes": sorted(reachable),
            "provenance": provenance,
            "socratic_gaps": [] if provenance else ["Capture supporting artefacts"],
        }
        return {"plan": plan, "dialectic": self.get_dialectic_log()}


class CriticAgent(BaseWSDESpecialist):
    """Challenges the research plan and validates provenance bindings."""

    def process(self, inputs: Mapping[str, object]) -> dict[str, object]:
        self._reset_dialectic()
        graph = self._require_graph_adapter(inputs)
        plan = inputs.get("plan")
        if not isinstance(plan, Mapping):
            raise ValueError("CriticAgent expects a plan produced by ResearchLeadAgent")

        start_node = str(
            inputs.get("start_node") or plan.get("start_node") or ""
        ).strip()
        baseline = set()
        if start_node:
            baseline = graph.traverse_graph(
                start_node, max_depth=2, include_research=False
            )

        critiques: list[dict[str, object]] = []
        for entry in plan.get("provenance", []):
            supports = entry.get("supports", ())
            derived = entry.get("derived_from", ())
            missing_support = not supports
            missing_derivation = not derived
            critiques.append(
                {
                    "artifact": entry.get("artifact"),
                    "requires_follow_up": bool(missing_support or missing_derivation),
                    "notes": (
                        "Evidence incomplete"
                        if missing_support or missing_derivation
                        else "Evidence sufficient"
                    ),
                }
            )

        approved = not any(item["requires_follow_up"] for item in critiques)
        verdict = "approved" if approved else "rework"
        self._record_exchange(
            role="Critic",
            claim="Research plan validation",
            question="Do artefacts withstand dialectical critique?",
            verdict=verdict,
            evidence=tuple(
                sorted(
                    {
                        entry.get("artifact")
                        for entry in plan.get("provenance", [])
                        if entry.get("artifact")
                    }
                )
            ),
        )

        return {
            "critiques": critiques,
            "baseline_neighbors": sorted(baseline),
            "approved": approved,
            "dialectic": self.get_dialectic_log(),
        }


class TestWriterAgent(BaseWSDESpecialist):
    """Translates approved artefacts into executable validation prompts."""

    def process(self, inputs: Mapping[str, object]) -> dict[str, object]:
        self._reset_dialectic()
        plan = inputs.get("plan")
        if not isinstance(plan, Mapping):
            raise ValueError("TestWriterAgent requires a research plan for context")

        critiques_input = inputs.get("critiques")
        critiques: Sequence[Mapping[str, object]]
        if isinstance(critiques_input, Sequence):
            critiques = tuple(
                entry for entry in critiques_input if isinstance(entry, Mapping)
            )
        else:
            critiques = ()

        blocked = any(entry.get("requires_follow_up") for entry in critiques)
        test_cases: list[dict[str, object]] = []
        for artifact in plan.get("provenance", []):
            supports = artifact.get("supports", ())
            derived = artifact.get("derived_from", ())
            for target in supports:
                test_cases.append(
                    {
                        "id": f"test_{target}",
                        "artifact": artifact.get("artifact"),
                        "assertion": f"Verify {target} remains supported by {artifact.get('artifact')}",
                        "derived_from": list(derived),
                    }
                )

        verdict = "blocked" if blocked else "ready"
        self._record_exchange(
            role="Test Writer",
            claim="Validation coverage",
            question="Are follow-up tests actionable?",
            verdict=verdict,
            evidence=tuple(case["id"] for case in test_cases),
        )

        return {
            "test_cases": test_cases,
            "blocked": blocked,
            "dialectic": self.get_dialectic_log(),
        }


def run_specialist_rotation(
    task: Mapping[str, object],
    graph_adapter: EnhancedGraphMemoryAdapter,
    start_node: str,
    agents: Sequence[BaseWSDESpecialist],
) -> dict[str, Mapping[str, object]]:
    """Execute a Research Lead → Critic → Test Writer rotation."""

    context: MutableMapping[str, object] = {
        "task": dict(task),
        "graph_adapter": graph_adapter,
        "start_node": start_node,
    }
    outputs: dict[str, Mapping[str, object]] = {}
    for agent in agents:
        result = agent.process(context)
        outputs[agent.__class__.__name__] = result
        context.update(result)
    return outputs


__all__ = [
    "DialecticalExchange",
    "ResearchLeadAgent",
    "CriticAgent",
    "TestWriterAgent",
    "run_specialist_rotation",
]
