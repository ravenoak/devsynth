"""Dialectical reasoning loop utilities for EDRR workflows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from devsynth.domain.models.wsde_dialectical import (
    apply_dialectical_reasoning as _apply_dialectical_reasoning,
)
from devsynth.exceptions import ConsensusError
from devsynth.logger import log_consensus_failure
from devsynth.logging_setup import DevSynthLogger

from ..base import Phase
from .coordinator import EDRRCoordinator

logger = DevSynthLogger(__name__)


def reasoning_loop(
    wsde_team: Any,
    task: Dict[str, Any],
    critic_agent: Any,
    memory_integration: Optional[Any] = None,
    *,
    phase: Phase = Phase.REFINE,
    max_iterations: int = 3,
    coordinator: Optional[EDRRCoordinator] = None,
) -> List[Dict[str, Any]]:
    """Iteratively apply dialectical reasoning until completion or failure."""
    results: List[Dict[str, Any]] = []
    current_task = task
    for iteration in range(max_iterations):
        logger.info("Dialectical reasoning iteration %s", iteration + 1)
        try:
            result = _apply_dialectical_reasoning(
                wsde_team, current_task, critic_agent, memory_integration
            )
        except ConsensusError as exc:  # pragma: no cover - logging path
            if coordinator is not None:
                coordinator.record_consensus_failure(exc)
            else:
                log_consensus_failure(logger, exc)
            break
        if coordinator is not None:
            record_map = {
                Phase.EXPAND: coordinator.record_expand_results,
                Phase.DIFFERENTIATE: coordinator.record_differentiate_results,
                Phase.REFINE: coordinator.record_refine_results,
            }
            record_map.get(phase, coordinator.record_refine_results)(result)
        results.append(result)
        if result.get("status") == "completed":
            break
        synthesis = result.get("synthesis")
        if synthesis is not None:
            current_task = {**current_task, "solution": synthesis}
    return results
