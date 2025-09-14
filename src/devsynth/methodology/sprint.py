"""Sprint methodology adapter for DevSynth.

This module implements integration between DevSynth's EDRR methodology
and traditional Agile sprint practices.
"""

import datetime
import time
from importlib import import_module
from typing import Any, Dict, List, Optional, cast
from collections.abc import Callable

from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import BaseMethodologyAdapter, Phase
from devsynth.methodology.sprint_adapter import (
    CEREMONY_PHASE_MAP,
    map_ceremony_to_phase,
)


def _map_requirements_to_plan(req_analysis: dict[str, Any]) -> dict[str, Any]:
    module = import_module("devsynth.application.sprint." + "planning")
    func = module.map_requirements_to_plan
    return cast(Callable[[dict[str, Any]], dict[str, Any]], func)(req_analysis)


def _map_retrospective_to_summary(
    results: dict[str, Any], sprint_number: int
) -> dict[str, Any]:
    module = import_module("devsynth.application.sprint." + "retrospective")
    func = module.map_retrospective_to_summary
    return cast(Callable[[dict[str, Any], int], dict[str, Any]], func)(
        results, sprint_number
    )


logger = DevSynthLogger(__name__)


class SprintAdapter(BaseMethodologyAdapter):
    """Adapter for integrating EDRR with Agile sprint practices.

    This adapter implements a time-boxed sprint approach to EDRR cycles,
    with configurable sprint duration and phase allocations.
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize the sprint adapter.

        Args:
            config: Configuration dictionary from the manifest.yaml file.
        """
        super().__init__(config)

        # Extract sprint-specific settings
        self.sprint_settings = self.config.get("settings", {})
        self.sprint_duration = self.sprint_settings.get("sprintDuration", 2)  # Weeks

        # Sprint state
        self.sprint_start_time = None
        self.sprint_end_time = None
        self.current_sprint_number = 0

        # Phase time allocations (percentage of sprint)
        self.phase_allocations = {
            Phase.EXPAND: self.sprint_settings.get("phaseAllocations", {}).get(
                "expand", 30
            ),
            Phase.DIFFERENTIATE: self.sprint_settings.get("phaseAllocations", {}).get(
                "differentiate", 30
            ),
            Phase.REFINE: self.sprint_settings.get("phaseAllocations", {}).get(
                "refine", 25
            ),
            Phase.RETROSPECT: self.sprint_settings.get("phaseAllocations", {}).get(
                "retrospect", 15
            ),
        }

        # Initialize metrics
        self.metrics = {
            "planned_scope": [],
            "actual_scope": [],
            "quality_metrics": {},
            "velocity": [],
            "retrospective_reviews": [],
            "inconsistencies_detected": [],
            "relationships_modeled": [],
        }

        # Map sprint ceremonies to their corresponding EDRR phases. Start with
        # default mappings and allow configuration to override them.
        self.ceremony_phase_map = dict(CEREMONY_PHASE_MAP)
        ceremony_mapping = self.sprint_settings.get("ceremonyMapping", {})
        for ceremony, target in ceremony_mapping.items():
            self.ceremony_phase_map[ceremony] = self._extract_phase_from_mapping(target)

    def should_start_cycle(self) -> bool:
        """Determine if a new sprint cycle should begin.

        A new sprint cycle should begin if:
        1. No sprint is currently active, or
        2. The current sprint has ended

        Returns:
            True if a new sprint cycle should begin, False otherwise.
        """
        if self.sprint_start_time is None:
            return True

        if self.sprint_end_time and datetime.datetime.now() > self.sprint_end_time:
            return True

        return False

    def should_progress_to_next_phase(
        self, current_phase: Phase, context: dict[str, Any], results: dict[str, Any]
    ) -> bool:
        """Determine if the process should progress to the next phase.

        In sprint methodology, phases progress based on time allocation and completion
        of required activities.

        Args:
            current_phase: The current EDRR phase.
            context: Context data for the current phase.
            results: Results from the current phase.

        Returns:
            True if the process should progress to the next phase, False otherwise.
        """
        if self.sprint_start_time is None:
            return False

        phase_start_time = context.get("phase_start_time")
        if not phase_start_time:
            return False

        expected_phase_end_time = self._calculate_phase_end_time(
            current_phase, phase_start_time
        )

        # Check if we've exceeded the time allocation
        if self._is_phase_time_exceeded(current_phase, phase_start_time):
            now = datetime.datetime.now()
            # Check if the phase has completed required activities
            required_activities = self._get_required_activities(current_phase)
            completed_activities = results.get("completed_activities", [])

            missing_activities = [
                a for a in required_activities if a not in completed_activities
            ]

            # If we're past the time but haven't completed required activities,
            # check if we're significantly over time
            if missing_activities:
                time_overrun = now - expected_phase_end_time
                max_overrun = datetime.timedelta(
                    hours=24
                )  # Allow up to 24 hours overrun

                # If we're significantly over time, force progression
                if time_overrun > max_overrun:
                    self._log_phase_timeout(current_phase, missing_activities)
                    return True

                return False

            return True

        # If we're within time allocation, check if all activities are complete
        required_activities = self._get_required_activities(current_phase)
        completed_activities = results.get("completed_activities", [])

        return all(a in completed_activities for a in required_activities)

    def before_cycle(self) -> dict[str, Any]:
        """Perform sprint planning before starting a new EDRR cycle.

        Returns:
            Context data for the new sprint.
        """
        # Increment sprint number
        self.current_sprint_number += 1

        # Set sprint timeframe
        self.sprint_start_time = datetime.datetime.now()
        self.sprint_end_time = self.sprint_start_time + datetime.timedelta(
            weeks=self.sprint_duration
        )

        # Prepare sprint context
        sprint_context = {
            "sprint_number": self.current_sprint_number,
            "sprint_start_time": self.sprint_start_time,
            "sprint_end_time": self.sprint_end_time,
            "sprint_duration_weeks": self.sprint_duration,
            "phase_allocations": {
                phase.value: alloc for phase, alloc in self.phase_allocations.items()
            },
        }

        # Add sprint planning details if available
        if hasattr(self, "sprint_plan") and self.sprint_plan:
            sprint_context["sprint_plan"] = self.sprint_plan

        return sprint_context

    def after_cycle(self, results: dict[str, Any]) -> None:
        """Perform sprint retrospective after completing an EDRR cycle.

        Args:
            results: Aggregated results from all phases.
        """
        # Capture velocity metrics
        completed_items = len(results.get("expand", {}).get("processed_artifacts", []))
        self.metrics["velocity"].append(
            {
                "sprint": self.current_sprint_number,
                "completed_items": completed_items,
                "duration_days": self.sprint_duration * 7,
            }
        )

        expand_results = results.get("expand", {})
        # Track actual scope delivered during the sprint
        self.metrics["actual_scope"].append(
            expand_results.get("processed_artifacts", [])
        )

        # Fallback: capture planning if after_expand was skipped
        if not getattr(self, "sprint_plan", None):
            req_analysis = expand_results.get("requirements_analysis")
            if req_analysis:
                self.sprint_plan = _map_requirements_to_plan(req_analysis)
                self.metrics["planned_scope"].append(
                    self.sprint_plan.get("planned_scope", [])
                )

        retrospect_results = results.get("retrospect", {})

        # Generate retrospective report
        self._generate_retrospective_report(results)

        # Reset sprint state
        self.sprint_start_time = None
        self.sprint_end_time = None

    def before_expand(self, context: dict[str, Any]) -> dict[str, Any]:
        """Sprint-specific setup before the Expand phase.

        Args:
            context: The current context.

        Returns:
            Updated context.
        """
        # Record phase start time
        context["phase_start_time"] = datetime.datetime.now()

        # Add planned scope from sprint planning
        if hasattr(self, "sprint_plan") and self.sprint_plan:
            context["planned_scope"] = self.sprint_plan.get("planned_scope", [])

        return context

    def after_expand(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Align sprint planning with requirement analysis results."""
        req_analysis = results.get("requirements_analysis")
        if req_analysis:
            self.sprint_plan = _map_requirements_to_plan(req_analysis)
            self.metrics["planned_scope"].append(
                self.sprint_plan.get("planned_scope", [])
            )
        return results

    def before_differentiate(self, context: dict[str, Any]) -> dict[str, Any]:
        """Sprint-specific setup before the Differentiate phase.

        Args:
            context: The current context.

        Returns:
            Updated context with phase start timestamp.
        """
        context["phase_start_time"] = datetime.datetime.now()
        return context

    def after_differentiate(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Record metrics after the Differentiate phase."""
        inconsistencies = results.get("inconsistencies")
        if inconsistencies is not None:
            self.metrics["inconsistencies_detected"].append(inconsistencies)
        return results

    def before_refine(self, context: dict[str, Any]) -> dict[str, Any]:
        """Sprint-specific setup before the Refine phase.

        Args:
            context: The current context.

        Returns:
            Updated context with phase start timestamp.
        """
        context["phase_start_time"] = datetime.datetime.now()
        return context

    def after_refine(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Record metrics after the Refine phase."""
        relationships = results.get("relationships")
        if relationships is not None:
            self.metrics["relationships_modeled"].append(relationships)
        return results

    def before_retrospect(self, context: dict[str, Any]) -> dict[str, Any]:
        """Sprint-specific setup before the Retrospect phase.

        Args:
            context: The current context.

        Returns:
            Updated context with phase start timestamp.
        """
        context["phase_start_time"] = datetime.datetime.now()
        return context

    def after_retrospect(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Sprint-specific activities after the Retrospect phase, including sprint planning.

        Args:
            context: Context data from the phase.
            results: Results from the phase.

        Returns:
            Updated results.
        """
        # Capture sprint planning for the next sprint
        self.sprint_plan = {
            "planned_scope": results.get("next_cycle_recommendations", {}).get(
                "scope", []
            ),
            "objectives": results.get("next_cycle_recommendations", {}).get(
                "objectives", []
            ),
            "success_criteria": results.get("next_cycle_recommendations", {}).get(
                "success_criteria", []
            ),
        }

        summary = _map_retrospective_to_summary(results, self.current_sprint_number)
        if summary:
            self.metrics["retrospective_reviews"].append(summary)

        evaluation = results.get("evaluation")
        if evaluation is not None:
            self.metrics["quality_metrics"][self.current_sprint_number] = evaluation

        return results

    def generate_reports(self, cycle_results: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate sprint reports from cycle results.

        Args:
            cycle_results: Results from the completed cycle.

        Returns:
            List of generated reports.
        """
        reports = []

        # Sprint review report
        review_report = {
            "title": f"Sprint {self.current_sprint_number} Review",
            "type": "sprint_review",
            "content": {
                "sprint_number": self.current_sprint_number,
                "duration": f"{self.sprint_duration} weeks",
                "start_date": self.sprint_start_time.strftime("%Y-%m-%d"),
                "end_date": self.sprint_end_time.strftime("%Y-%m-%d"),
                "completed_scope": cycle_results.get("actual_scope", []),
                "key_metrics": {
                    "artifacts_processed": len(
                        cycle_results.get("expand", {}).get("processed_artifacts", [])
                    ),
                    "inconsistencies_detected": len(
                        cycle_results.get("differentiate", {}).get(
                            "inconsistencies", []
                        )
                    ),
                    "relationship_count": len(
                        cycle_results.get("refine", {}).get("relationships", [])
                    ),
                    "insights_generated": len(
                        cycle_results.get("retrospect", {}).get("insights", [])
                    ),
                },
            },
        }
        reports.append(review_report)

        # Sprint retrospective report
        retro_report = {
            "title": f"Sprint {self.current_sprint_number} Retrospective",
            "type": "sprint_retrospective",
            "content": {
                "sprint_number": self.current_sprint_number,
                "what_went_well": cycle_results.get("retrospect", {}).get(
                    "positives", []
                ),
                "what_could_improve": cycle_results.get("retrospect", {}).get(
                    "improvements", []
                ),
                "action_items": cycle_results.get("retrospect", {}).get(
                    "action_items", []
                ),
            },
        }
        reports.append(retro_report)

        return reports

    def get_config_schema(self) -> dict[str, Any]:
        """Get JSON schema for sprint configuration validation.

        Returns:
            JSON schema dictionary.
        """
        base_schema = super().get_config_schema()

        # Add sprint-specific configuration options
        sprint_schema = {
            "type": "object",
            "properties": {
                "settings": {
                    "type": "object",
                    "properties": {
                        "sprintDuration": {
                            "type": "number",
                            "description": "Sprint duration in weeks",
                            "default": 2,
                            "minimum": 0.5,
                            "maximum": 4,
                        },
                        "phaseAllocations": {
                            "type": "object",
                            "properties": {
                                phase.value: {
                                    "type": "number",
                                    "description": f"Percentage of sprint allocated to {phase.value} phase",
                                    "minimum": 5,
                                    "maximum": 70,
                                }
                                for phase in Phase
                            },
                        },
                        "ceremonyMapping": {
                            "type": "object",
                            "properties": {
                                "planning": {"type": "string"},
                                "dailyStandup": {"type": "string"},
                                "review": {"type": "string"},
                                "retrospective": {"type": "string"},
                            },
                        },
                    },
                }
            },
        }

        # Merge the schemas
        base_schema["properties"].update(sprint_schema["properties"])

        return base_schema

    def _calculate_phase_duration_seconds(self, phase: Phase) -> float:
        """Calculate the allotted duration for a phase in seconds."""
        sprint_seconds = self.sprint_duration * 7 * 24 * 60 * 60
        allocation_pct = self.phase_allocations[phase] / 100
        return sprint_seconds * allocation_pct

    def _calculate_phase_end_time(
        self, phase: Phase, start_time: datetime.datetime
    ) -> datetime.datetime:
        """Return the expected end time for a phase."""
        duration = self._calculate_phase_duration_seconds(phase)
        return start_time + datetime.timedelta(seconds=duration)

    def _is_phase_time_exceeded(
        self, phase: Phase, start_time: datetime.datetime
    ) -> bool:
        """Check if a phase has exceeded its allocated time."""
        return datetime.datetime.now() > self._calculate_phase_end_time(
            phase, start_time
        )

    def _get_required_activities(self, phase: Phase) -> list[str]:
        """Get required activities for a phase.

        Args:
            phase: The phase to get required activities for.

        Returns:
            List of required activity identifiers.
        """
        # This would typically come from configuration, but we'll hardcode for example
        required_activities = {
            Phase.EXPAND: [
                "discovery_complete",
                "classification_complete",
                "extraction_complete",
            ],
            Phase.DIFFERENTIATE: ["validation_complete", "gap_analysis_complete"],
            Phase.REFINE: [
                "context_merging_complete",
                "relationship_modeling_complete",
            ],
            Phase.RETROSPECT: [
                "evaluation_complete",
                "insight_capture_complete",
                "planning_complete",
            ],
        }

        return required_activities.get(phase, [])

    def _log_phase_timeout(self, phase: Phase, missing_activities: list[str]) -> None:
        """Log a timeout event for a phase.

        Args:
            phase: The phase that timed out.
            missing_activities: Activities that were not completed.
        """
        logger.warning(
            "Phase %s timed out with %d activities incomplete",
            phase.value,
            len(missing_activities),
        )
        logger.warning("Missing activities: %s", ", ".join(missing_activities))

    def _generate_retrospective_report(self, results: dict[str, Any]) -> None:
        """Generate a retrospective report from sprint results.

        Args:
            results: Aggregated results from all phases.
        """
        logger.info("Sprint %d Retrospective", self.current_sprint_number)
        logger.info("Duration: %d weeks", self.sprint_duration)
        logger.info(
            "Items completed: %d",
            len(results.get("expand", {}).get("processed_artifacts", [])),
        )
        logger.info(
            "Inconsistencies identified: %d",
            len(results.get("differentiate", {}).get("inconsistencies", [])),
        )
        logger.info(
            "Relationships modeled: %d",
            len(results.get("refine", {}).get("relationships", [])),
        )
        logger.info(
            "Insights generated: %d",
            len(results.get("retrospect", {}).get("insights", [])),
        )

    def get_ceremony_phase(self, ceremony: str) -> Phase | None:
        """Return the EDRR phase associated with an Agile ceremony.

        Args:
            ceremony: Name of the ceremony (e.g., ``planning`` or ``review``).

        Returns:
            ``Phase`` enum if the ceremony maps to a known phase, otherwise ``None``.
        """
        phase = self.ceremony_phase_map.get(ceremony)
        if phase is not None:
            return phase
        # Fallback to helper for any ceremony not explicitly configured.
        return map_ceremony_to_phase(ceremony)

    def _extract_phase_from_mapping(self, mapping: str) -> Phase | None:
        """Extract an EDRR phase from a ceremony mapping string.

        The mapping string may refer to a phase directly (``"refine"``) or include
        a sub-phase path such as ``"retrospect.iteration_planning"``. If no known
        phase can be identified, ``None`` is returned.

        Args:
            mapping: Configuration string representing the target phase.

        Returns:
            ``Phase`` instance or ``None`` if the mapping is unknown.
        """
        if not mapping:
            return None

        normalized = mapping.lower()
        for phase in Phase:
            if phase.value in normalized:
                return phase

        return map_ceremony_to_phase(normalized)
