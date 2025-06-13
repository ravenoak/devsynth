"""Extended WSDE team utilities."""

from typing import Any, Dict, List

from devsynth.domain.models.wsde import WSDETeam


class CollaborativeWSDETeam(WSDETeam):
    """WSDETeam with convenience methods for collaboration."""

    def collaborative_decision(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a collaborative voting process for a critical decision task."""
        return self.vote_on_critical_decision(task)

    def peer_review_solution(self, work_product: Any, author: Any) -> Dict[str, Any]:
        """Conduct a full peer review cycle for a work product."""
        reviewers = [a for a in self.agents if a is not author]
        return self.conduct_peer_review(work_product, author, reviewers)
