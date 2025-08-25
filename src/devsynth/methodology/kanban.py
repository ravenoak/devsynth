"""Kanban methodology adapter for DevSynth.

This adapter integrates the EDRR process with a continuous Kanban flow.
"""

import datetime
from typing import Any, Dict

from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import BaseMethodologyAdapter, Phase

logger = DevSynthLogger(__name__)


class KanbanAdapter(BaseMethodologyAdapter):
    """Adapter for integrating EDRR with a Kanban-style workflow."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        settings = self.config.get("settings", {})
        default_limit = 2
        self.wip_limits = {
            phase: settings.get("wipLimits", {}).get(phase.value, default_limit)
            for phase in Phase
        }
        self.board_state = {phase: 0 for phase in Phase}

    def should_start_cycle(self) -> bool:
        """Kanban flow always allows new items to enter the pipeline."""
        return True

    def should_progress_to_next_phase(
        self, current_phase: Phase, context: Dict[str, Any], results: Dict[str, Any]
    ) -> bool:
        """Move work forward if the next phase has capacity."""
        if not results.get("phase_complete"):
            return False
        next_phase = self._next_phase(current_phase)
        if self.board_state[next_phase] >= self.wip_limits.get(
            next_phase, float("inf")
        ):
            return False
        self.board_state[current_phase] = max(0, self.board_state[current_phase] - 1)
        self.board_state[next_phase] += 1
        return True

    def before_cycle(self) -> Dict[str, Any]:
        self.board_state = {phase: 0 for phase in Phase}
        return {"board_initialized": datetime.datetime.now().isoformat()}

    def after_cycle(self, results: Dict[str, Any]) -> None:
        results["cycle_closed"] = True
        self.board_state = {phase: 0 for phase in Phase}

    def generate_reports(self, cycle_results: Dict[str, Any]):
        return [
            {
                "title": "Kanban Flow Summary",
                "type": "kanban_summary",
                "content": {"wip": {p.value: c for p, c in self.board_state.items()}},
            }
        ]

    def _next_phase(self, phase: Phase) -> Phase:
        order = [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]
        return order[(order.index(phase) + 1) % len(order)]
