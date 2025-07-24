"""Milestone methodology adapter for DevSynth.

This adapter integrates EDRR with milestone-based development requiring formal approvals.
"""

import datetime
from typing import Any, Dict

from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import BaseMethodologyAdapter, Phase

logger = DevSynthLogger(__name__)


class MilestoneAdapter(BaseMethodologyAdapter):
    """Adapter for milestone-driven workflows with approval gates."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        settings = self.config.get("settings", {})
        self.approval_required = settings.get("approvalRequired", {})
        self.approvers = settings.get("approvers", [])

    def should_start_cycle(self) -> bool:
        return True

    def should_progress_to_next_phase(
        self, current_phase: Phase, context: Dict[str, Any], results: Dict[str, Any]
    ) -> bool:
        if not results.get("phase_complete"):
            return False
        key = f"after{current_phase.name.title()}"
        if self.approval_required.get(key, False):
            return results.get("approved", False)
        return True

    def before_cycle(self) -> Dict[str, Any]:
        return {"milestone_start": datetime.datetime.now().isoformat()}

    def after_cycle(self, results: Dict[str, Any]) -> None:
        results["milestone_complete"] = True

    def generate_reports(self, cycle_results: Dict[str, Any]):
        return [
            {
                "title": "Milestone Compliance Report",
                "type": "milestone_report",
                "content": {
                    "approvers": self.approvers,
                    "approval_required": self.approval_required,
                },
            }
        ]
