"""WSDE application wrapper providing collaboration helpers."""

from typing import Any, Dict, Optional
from collections.abc import Mapping

from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.domain.wsde.workflow import progress_roles as _progress_roles
from devsynth.logger import log_consensus_failure
from devsynth.methodology.base import Phase

from .dto import ConsensusOutcome


class WSDE(WSDETeam):
    """Application-facing WSDE team with utility methods."""

    def reassign_roles(self, task: dict[str, Any]) -> dict[str, Any]:
        """Reassign roles dynamically using task context."""
        return self.dynamic_role_reassignment(task)

    def run_consensus(self, task: dict[str, Any]) -> dict[str, Any]:
        """Perform a consensus vote and fallback to consensus building."""
        result = self.consensus_vote(task)
        decision = result.get("decision") or result.get("result")

        consensus_outcome: ConsensusOutcome | None = None
        existing_consensus = result.get("consensus")
        if isinstance(existing_consensus, ConsensusOutcome):
            consensus_outcome = existing_consensus
        elif isinstance(existing_consensus, Mapping):
            consensus_outcome = ConsensusOutcome.from_dict(existing_consensus)

        if not decision or result.get("status") != "completed":
            error = RuntimeError("Consensus vote failed")
            log_consensus_failure(self.logger, error, extra={"task_id": task.get("id")})
            consensus_outcome = self.build_consensus(task)

        if consensus_outcome is not None:
            result["consensus_outcome"] = consensus_outcome
            result["consensus"] = consensus_outcome.to_dict()

        return result

    def get_role_assignments(self) -> dict[str, str]:
        """Return a mapping of agent identifiers to their assigned roles."""

        name_map = self.get_role_map()
        assignments: dict[str, str] = {}
        for agent in self.agents:
            agent_id = getattr(agent, "id", None) or getattr(agent, "name", None)
            role = name_map.get(getattr(agent, "name", None)) or getattr(
                agent, "current_role", None
            )
            assignments[agent_id] = role
        return assignments

    def progress_roles(
        self, phase: Phase, memory_manager: object | None = None
    ) -> dict[str, str]:
        """Advance roles for the given phase and flush memory."""

        return _progress_roles(self, phase, memory_manager)
