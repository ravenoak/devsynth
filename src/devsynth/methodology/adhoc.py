"""Ad-hoc methodology adapter for DevSynth.

This module implements a flexible, on-demand approach to EDRR phases
for teams without a formal process or individual contributors.
"""

import datetime
from typing import Any, Dict, List, Optional

from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import BaseMethodologyAdapter, Phase

logger = DevSynthLogger(__name__)


class AdHocAdapter(BaseMethodologyAdapter):
    """Adapter for flexible, on-demand EDRR execution.

    This adapter allows phases to be run individually or in sequence
    without enforcing timing or ceremonial requirements. Ideal for:

    - Individual contributors
    - Exploratory work
    - Teams without formal processes
    - Specialized or targeted analysis
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the ad-hoc adapter.

        Args:
            config: Configuration dictionary from the manifest.yaml file.
        """
        super().__init__(config)

        # Extract ad-hoc specific settings
        self.adhoc_settings = self.config.get("settings", {})

        # Track completed phases and phase execution history
        self.completed_phases: set[Phase] = set()
        self.phase_history: list[dict[str, Any]] = []

        # Track if a cycle is currently in progress
        self.cycle_in_progress: bool = False

        # Optional callback for phase completion notification
        self.completion_callback: Any = self.adhoc_settings.get("completionCallback")
        self.phase_results: dict[Phase, dict[str, Any]] = {}

    def should_start_cycle(self) -> bool:
        """Determine if a new cycle should begin.

        For ad-hoc execution, a new cycle begins when:
        1. No cycle is currently in progress, and
        2. User has requested a new cycle (via config, CLI, or API)

        Returns:
            True if a new cycle should begin, False otherwise.
        """
        # This would typically be triggered by user action, but for example
        # we'll check a setting in the config
        user_requested = self.adhoc_settings.get("startNewCycle", False)

        return not self.cycle_in_progress and user_requested

    def should_progress_to_next_phase(
        self, current_phase: Phase, context: Dict[str, Any], results: Dict[str, Any]
    ) -> bool:
        """Determine if the process should progress to the next phase.

        For ad-hoc execution, phase progression occurs when:
        1. The current phase is marked as complete by the user or code, and
        2. The user has requested progression (via config, CLI, or API)

        Args:
            current_phase: The current EDRR phase.
            context: Context data for the current phase.
            results: Results from the current phase.

        Returns:
            True if the process should progress to the next phase, False otherwise.
        """
        # Check if phase is complete
        phase_complete = results.get("phase_complete", False)

        # Check if user requested progression
        user_requested = context.get("progress_to_next", False)

        # For ad-hoc mode, both must be true to progress
        if phase_complete and user_requested:
            self.completed_phases.add(current_phase)
            self.phase_history.append(
                {
                    "phase": current_phase.value,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "results_summary": self._summarize_results(results),
                }
            )
            return True

        return False

    def before_cycle(self) -> Dict[str, Any]:
        """Perform setup before starting a new EDRR cycle.

        Returns:
            Context data for the new cycle.
        """
        # Reset state
        self.completed_phases = set()
        self.phase_history = []
        self.cycle_in_progress = True

        # Prepare cycle context
        cycle_context = {
            "start_time": datetime.datetime.now().isoformat(),
            "mode": "ad-hoc",
            "scope": self.adhoc_settings.get("scope", "user-defined"),
        }

        return cycle_context

    def after_cycle(self, results: Dict[str, Any]) -> None:
        """Perform wrap-up after completing an EDRR cycle.

        Args:
            results: Aggregated results from all phases.
        """
        # Mark cycle as complete
        self.cycle_in_progress = False

        # Record cycle completion
        results["cycle_completed"] = True
        results["completion_time"] = datetime.datetime.now().isoformat()
        results["phases_executed"] = [p.value for p in self.completed_phases]

        # Call completion callback if defined
        if self.completion_callback:
            try:
                self.completion_callback(results)
            except Exception as e:
                logger.exception("Error in completion callback: %s", e)

    def before_phase(self, phase: Phase, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup before entering any phase.

        Args:
            phase: The phase about to begin.
            context: The current context.

        Returns:
            Updated context.
        """
        # Call the parent implementation first
        context = super().before_phase(phase, context)

        # Record phase start time and reset phase-specific flags
        context["phase_start_time"] = datetime.datetime.now().isoformat()
        context["progress_to_next"] = (
            False  # Must be explicitly set to True by user/code
        )

        return context

    def after_phase(
        self, phase: Phase, context: Dict[str, Any], results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Wrap-up after completing any phase.

        Args:
            phase: The completed phase.
            context: Context data from the phase.
            results: Results from the phase.

        Returns:
            Updated results.
        """
        # Call the parent implementation first
        results = super().after_phase(phase, context, results)

        # Record phase completion time
        results["phase_end_time"] = datetime.datetime.now().isoformat()

        # Set default status if not already set
        if "phase_complete" not in results:
            # In ad-hoc mode, we assume phase is complete once it runs
            results["phase_complete"] = True

        # Save results for later reference
        self.phase_results[phase] = results

        return results

    def generate_reports(self, cycle_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate reports from cycle results.

        For ad-hoc execution, reports are more focused on executed steps
        and findings rather than process conformance.

        Args:
            cycle_results: Results from the completed cycle.

        Returns:
            List of generated reports.
        """
        reports = []

        # Execution summary report
        summary_report = {
            "title": "Ad-hoc Execution Summary",
            "type": "execution_summary",
            "content": {
                "start_time": cycle_results.get("start_time"),
                "completion_time": cycle_results.get("completion_time"),
                "phases_executed": cycle_results.get("phases_executed", []),
                "phase_history": self.phase_history,
                "findings_summary": {
                    "artifacts_processed": len(
                        cycle_results.get("expand", {}).get("processed_artifacts", [])
                    ),
                    "inconsistencies_detected": len(
                        cycle_results.get("differentiate", {}).get(
                            "inconsistencies", []
                        )
                    ),
                    "relationships_identified": len(
                        cycle_results.get("refine", {}).get("relationships", [])
                    ),
                    "insights_generated": len(
                        cycle_results.get("retrospect", {}).get("insights", [])
                    ),
                },
            },
        }
        reports.append(summary_report)

        return reports

    def get_config_schema(self) -> Dict[str, Any]:
        """Get JSON schema for ad-hoc configuration validation.

        Returns:
            JSON schema dictionary.
        """
        base_schema = super().get_config_schema()

        # Add ad-hoc specific configuration options
        adhoc_schema = {
            "type": "object",
            "properties": {
                "settings": {
                    "type": "object",
                    "properties": {
                        "startNewCycle": {
                            "type": "boolean",
                            "description": "Flag to start a new cycle",
                            "default": False,
                        },
                        "scope": {
                            "type": "string",
                            "description": "Scope definition for the analysis",
                        },
                        "completionCallback": {
                            "type": "string",
                            "description": "Python dotted path to a callback function to call when cycle completes",
                        },
                        "enableIndividualPhaseExecution": {
                            "type": "boolean",
                            "description": "Allow phases to be run independently without requiring a full cycle",
                            "default": True,
                        },
                    },
                }
            },
        }

        # Merge the schemas
        base_schema["properties"].update(adhoc_schema["properties"])

        return base_schema

    def _summarize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a brief summary of phase results.

        Args:
            results: The full results dictionary.

        Returns:
            A summarized version with key metrics.
        """
        # Extract only essential information for history tracking
        summary = {}

        if "artifacts_count" in results:
            summary["artifacts_count"] = results["artifacts_count"]

        if "inconsistencies" in results:
            summary["inconsistencies_count"] = len(results["inconsistencies"])

        if "relationships" in results:
            summary["relationships_count"] = len(results["relationships"])

        if "insights" in results:
            summary["insights_count"] = len(results["insights"])

        return summary
