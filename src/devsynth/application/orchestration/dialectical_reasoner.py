"""Dialectical reasoning orchestrator with consensus failure logging."""

from typing import Any, Dict, Optional

from devsynth.exceptions import ConsensusError
from devsynth.logger import log_consensus_failure
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class DialecticalReasoner:
    """Run dialectical reasoning via an EDRR coordinator."""

    def __init__(self, coordinator: Any) -> None:
        self.coordinator = coordinator

    def run(
        self,
        task: Dict[str, Any],
        critic_agent: Any,
        memory_integration: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute dialectical reasoning and log consensus failures."""
        try:
            return self.coordinator.apply_dialectical_reasoning(
                task, critic_agent, memory_integration
            )
        except ConsensusError as exc:  # pragma: no cover - logging path
            log_consensus_failure(logger, exc)
            return None
