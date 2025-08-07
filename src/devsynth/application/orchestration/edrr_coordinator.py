"""EDRR coordinator with dialectical reasoning integration."""

from typing import Any, Dict, Optional

from devsynth.domain.models.wsde_dialectical import (
    apply_dialectical_reasoning as _apply_dialectical_reasoning,
)
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class EDRRCoordinator:
    """Coordinate EDRR cycles with dialectical reasoning helpers."""

    def __init__(self, wsde_team: Any) -> None:
        self.wsde_team = wsde_team

    def apply_dialectical_reasoning(
        self,
        task: Dict[str, Any],
        critic_agent: Any,
        memory_integration: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Delegate dialectical reasoning to WSDE helpers.

        Args:
            task: Task containing a proposed solution.
            critic_agent: Agent providing critiques.
            memory_integration: Optional memory component.

        Returns:
            Result from :func:`apply_dialectical_reasoning`.
        """
        logger.info("EDRRCoordinator invoking dialectical reasoning")
        return _apply_dialectical_reasoning(
            self.wsde_team, task, critic_agent, memory_integration
        )
