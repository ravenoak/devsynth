"""Base methodology adapter for DevSynth.

This module provides the foundation for integrating DevSynth's EDRR methodology
with different development workflows and practices.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any, cast


class Phase(Enum):
    """Enumeration of EDRR phases."""

    EXPAND = "expand"
    DIFFERENTIATE = "differentiate"
    REFINE = "refine"
    RETROSPECT = "retrospect"

    # Additional phases used by specialized workflows. These are aliases that
    # map to intermediate steps outside of the core EDRR cycle but are useful
    # for tests and extension points.
    ANALYSIS = "analysis"
    IMPLEMENTATION = "implementation"
    REFINEMENT = "refinement"


class BaseMethodologyAdapter(ABC):
    """Base class for methodology adapters.

    A methodology adapter integrates DevSynth's EDRR process with a team's
    preferred development workflow. It handles timing, progression logic,
    and integration with external tools while maintaining the logical
    sequence of the EDRR phases.
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize the methodology adapter.

        Args:
            config: Configuration dictionary from the manifest.yaml file.
        """
        self.config = config
        self.current_phase: Phase | None = None
        self.phase_results: dict[Phase, dict[str, Any]] = {}

    @abstractmethod
    def should_start_cycle(self) -> bool:
        """Determine if a new EDRR cycle should begin.

        Returns:
            True if a new cycle should begin, False otherwise.
        """
        raise NotImplementedError(
            "should_start_cycle must be implemented by subclasses"
        )

    @abstractmethod
    def should_progress_to_next_phase(
        self, current_phase: Phase, context: dict[str, Any], results: dict[str, Any]
    ) -> bool:
        """Determine if the process should progress to the next phase.

        Args:
            current_phase: The current EDRR phase.
            context: Context data for the current phase.
            results: Results from the current phase.

        Returns:
            True if the process should progress to the next phase, False otherwise.
        """
        raise NotImplementedError(
            "should_progress_to_next_phase must be implemented by subclasses"
        )

    def before_cycle(self) -> dict[str, Any]:
        """Perform actions before starting a new EDRR cycle.

        Returns:
            Context data for the new cycle.
        """
        return {}

    def after_cycle(self, results: dict[str, Any]) -> None:
        """Perform actions after completing an EDRR cycle.

        Args:
            results: Aggregated results from all phases.
        """
        raise NotImplementedError("after_cycle must be implemented by subclasses")

    def before_phase(self, phase: Phase, context: dict[str, Any]) -> dict[str, Any]:
        """Perform actions before entering a phase.

        Args:
            phase: The phase about to begin.
            context: Context data for the current cycle.

        Returns:
            Updated context data for the phase.
        """
        phase_method = getattr(self, f"before_{phase.value}", None)
        if callable(phase_method):
            method = cast(Callable[[dict[str, Any]], dict[str, Any]], phase_method)
            return method(context)
        return context

    def after_phase(
        self, phase: Phase, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Perform actions after completing a phase.

        Args:
            phase: The completed phase.
            context: Context data from the phase.
            results: Results from the phase.

        Returns:
            Updated results.
        """
        phase_method = getattr(self, f"after_{phase.value}", None)
        if callable(phase_method):
            method = cast(
                Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
                phase_method,
            )
            return method(context, results)
        return results

    def register_external_events(self) -> list[dict[str, Any]]:
        """Register for external events/webhooks if needed.

        Returns:
            List of registered event handlers.
        """
        return []

    def generate_reports(self, cycle_results: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate reports from cycle results.

        Args:
            cycle_results: Results from the completed cycle.

        Returns:
            List of generated reports.
        """
        return []

    def get_metadata(self) -> dict[str, Any]:
        """Get metadata about the methodology.

        Returns:
            Dictionary with methodology metadata.
        """
        return {
            "name": self.__class__.__name__,
            "description": self.__doc__,
            "config_schema": self.get_config_schema(),
        }

    def get_config_schema(self) -> dict[str, Any]:
        """Get JSON schema for configuration validation.

        Returns:
            JSON schema dictionary.
        """
        return {
            "type": "object",
            "properties": {
                "phases": {
                    "type": "object",
                    "properties": {
                        phase.value: {
                            "type": "object",
                            "properties": {
                                "skipable": {"type": "boolean"},
                                "customHooks": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        }
                        for phase in Phase
                    },
                }
            },
        }

    # These methods can be overridden by subclasses for phase-specific behavior
    def before_expand(self, context: dict[str, Any]) -> dict[str, Any]:
        """Actions before the Expand phase."""
        return context

    def after_expand(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Actions after the Expand phase."""
        return results

    def before_differentiate(self, context: dict[str, Any]) -> dict[str, Any]:
        """Actions before the Differentiate phase."""
        return context

    def after_differentiate(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Actions after the Differentiate phase."""
        return results

    def before_refine(self, context: dict[str, Any]) -> dict[str, Any]:
        """Actions before the Refine phase."""
        return context

    def after_refine(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Actions after the Refine phase."""
        return results

    def before_retrospect(self, context: dict[str, Any]) -> dict[str, Any]:
        """Actions before the Retrospect phase."""
        return context

    def after_retrospect(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Actions after the Retrospect phase."""
        return results

    def before_analysis(self, context: dict[str, Any]) -> dict[str, Any]:
        """Actions before the Analysis phase."""
        return context

    def after_analysis(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Actions after the Analysis phase."""
        return results

    def before_implementation(self, context: dict[str, Any]) -> dict[str, Any]:
        """Actions before the Implementation phase."""
        return context

    def after_implementation(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Actions after the Implementation phase."""
        return results

    def before_refinement(self, context: dict[str, Any]) -> dict[str, Any]:
        """Actions before the Refinement phase."""
        return context

    def after_refinement(
        self, context: dict[str, Any], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Actions after the Refinement phase."""
        return results
