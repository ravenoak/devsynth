"""WSDE application wrapper providing collaboration helpers."""

from typing import Any, Dict

from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


class WSDE(WSDETeam):
    """Application-facing WSDE team with utility methods."""

    def reassign_roles(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Reassign roles dynamically using task context."""
        return self.dynamic_role_reassignment(task)

    def run_consensus(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a consensus vote and fallback to consensus building."""
        result = self.consensus_vote(task)
        decision = result.get("decision") or result.get("result")
        if not decision or result.get("status") != "completed":
            result["consensus"] = self.build_consensus(task)
        return result

    def get_role_assignments(self) -> Dict[str, str]:
        """Return a mapping of agent identifiers to their assigned roles."""

        return self.get_role_map()
