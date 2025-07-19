"""
Enhanced EDRR Coordinator with improved phase transitions.

This module extends the EDRRCoordinator class with enhanced phase transition
logic, quality scoring, and metrics collection.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.application.edrr.edrr_phase_transitions import (
    PhaseTransitionMetrics,
    calculate_enhanced_quality_score,
    collect_phase_metrics,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.domain.models.memory import MemoryType
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase

logger = DevSynthLogger(__name__)


class EnhancedEDRRCoordinator(EDRRCoordinator):
    """
    Enhanced EDRR Coordinator with improved phase transitions.

    This class extends the EDRRCoordinator with enhanced phase transition logic,
    quality scoring, and metrics collection.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        wsde_team: WSDETeam,
        code_analyzer: CodeAnalyzer,
        ast_transformer: AstTransformer,
        prompt_manager: PromptManager,
        documentation_manager: DocumentationManager,
        enable_enhanced_logging: bool = False,
        parent_cycle_id: str = None,
        recursion_depth: int = 0,
        parent_phase: Phase = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the EnhancedEDRRCoordinator.

        Args:
            memory_manager: The memory manager to use
            wsde_team: The WSDE team to use
            code_analyzer: The code analyzer to use
            ast_transformer: The AST transformer to use
            prompt_manager: The prompt manager to use
            documentation_manager: The documentation manager to use
            enable_enhanced_logging: Whether to enable enhanced logging
            parent_cycle_id: The ID of the parent cycle, if this is a micro-cycle
            recursion_depth: The recursion depth of this cycle
            parent_phase: The phase of the parent cycle that created this cycle
            config: Optional configuration dictionary
        """
        super().__init__(
            memory_manager=memory_manager,
            wsde_team=wsde_team,
            code_analyzer=code_analyzer,
            ast_transformer=ast_transformer,
            prompt_manager=prompt_manager,
            documentation_manager=documentation_manager,
            enable_enhanced_logging=enable_enhanced_logging,
            parent_cycle_id=parent_cycle_id,
            recursion_depth=recursion_depth,
            parent_phase=parent_phase,
            config=config,
        )

        # Initialize phase transition metrics
        self.phase_metrics = PhaseTransitionMetrics()

        # Enhanced configuration
        self.config = config or {}
        self.auto_phase_transitions = self.config.get("auto_phase_transitions", True)
        self.quality_based_transitions = self.config.get(
            "quality_based_transitions", True
        )
        self.phase_transition_timeout = self.config.get(
            "phase_transition_timeout", 3600
        )  # 1 hour default

    def progress_to_phase(self, phase: Phase) -> None:
        """
        Progress to the specified phase with enhanced metrics collection.

        Args:
            phase: The phase to progress to

        Raises:
            EDRRCoordinatorError: If the phase dependencies are not met
        """
        try:
            # Record the start of the phase in metrics
            self.phase_metrics.start_phase(phase)

            # Call the parent implementation
            super().progress_to_phase(phase)

            # Collect metrics for the phase
            phase_results = self.results.get(phase.name, {})
            metrics = collect_phase_metrics(phase, phase_results)

            # Record the end of the phase in metrics
            self.phase_metrics.end_phase(phase, metrics)

            # Store the metrics in memory
            metrics_metadata = {"cycle_id": self.cycle_id, "type": "PHASE_METRICS"}
            self._safe_store_with_edrr_phase(
                metrics, MemoryType.EPISODIC, phase.value, metrics_metadata
            )

            # Log the metrics
            logger.info(f"Phase {phase.name} metrics: {metrics}")

            # Automatically transition to next phase if enabled and conditions are met
            self._enhanced_maybe_auto_progress()
        except Exception as e:
            logger.error(f"Failed to progress to phase {phase.value}: {e}")
            raise EDRRCoordinatorError(
                f"Failed to progress to phase {phase.value}: {e}"
            )

    def _enhanced_decide_next_phase(self) -> Optional[Phase]:
        """
        Determine if the coordinator should automatically move to the next phase.

        This enhanced version considers quality metrics in addition to timeouts.

        Returns:
            The next phase to transition to, or None if no transition should occur
        """
        if not self.auto_phase_transitions:
            return None

        if self.current_phase == Phase.RETROSPECT:
            return None

        phase_order = [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]
        idx = phase_order.index(self.current_phase)
        next_phase = phase_order[idx + 1]

        # Check if the phase is explicitly marked as complete
        phase_results = self.results.get(self.current_phase.name, {})
        if phase_results.get("phase_complete", False) is True:
            logger.info(
                f"Phase {self.current_phase.name} explicitly marked as complete"
            )
            return next_phase

        # Check quality-based transition if enabled
        if self.quality_based_transitions:
            should_transition, reasons = self.phase_metrics.should_transition(
                self.current_phase
            )
            if should_transition:
                logger.info(
                    f"Quality metrics indicate phase {self.current_phase.name} should transition: {reasons}"
                )
                return next_phase
            else:
                logger.debug(
                    f"Quality metrics indicate phase {self.current_phase.name} should not transition: {reasons}"
                )

        # Check timeout-based transition
        start_time = self._phase_start_times.get(self.current_phase)
        if (
            start_time
            and (datetime.now() - start_time).total_seconds()
            >= self.phase_transition_timeout
        ):
            logger.info(
                f"Phase {self.current_phase.name} timed out after {self.phase_transition_timeout} seconds"
            )
            return next_phase

        return None

    def _enhanced_maybe_auto_progress(self) -> None:
        """
        Trigger automatic phase transition when conditions are met.

        This enhanced version uses the enhanced decision logic.
        Includes safeguards against infinite loops:
        - Maximum iteration count
        - Guard against re-entering during active transition
        """
        if not self.auto_phase_transitions:
            return

        # Guard against re-entering during active transition
        if getattr(self, "_in_auto_progress", False):
            logger.warning(
                "Prevented re-entry into auto-progress during active transition"
            )
            return

        try:
            # Set guard flag
            self._in_auto_progress = True

            # Maximum number of iterations to prevent infinite loops
            max_iterations = 4  # Maximum phases in EDRR cycle
            iteration_count = 0

            while iteration_count < max_iterations:
                iteration_count += 1
                logger.debug(
                    f"Auto-progress iteration {iteration_count}/{max_iterations}"
                )

                next_phase = self._enhanced_decide_next_phase()
                if not next_phase:
                    logger.debug("No next phase determined, stopping auto-progress")
                    break

                logger.info(
                    f"Auto-progressing from {self.current_phase.name} to {next_phase.name} (iteration {iteration_count})"
                )

                # Call parent's progress_to_phase to avoid recursive call to _enhanced_maybe_auto_progress
                super().progress_to_phase(next_phase)

                # Update metrics manually since we're bypassing our own progress_to_phase
                phase_results = self.results.get(next_phase.name, {})
                metrics = collect_phase_metrics(next_phase, phase_results)
                self.phase_metrics.end_phase(next_phase, metrics)

            if iteration_count >= max_iterations:
                logger.warning(
                    f"Reached maximum auto-progress iterations ({max_iterations}), stopping to prevent potential infinite loop"
                )
        finally:
            # Always clear the guard flag
            self._in_auto_progress = False

    def _calculate_quality_score(self, result: Any) -> float:
        """
        Calculate a quality score for a result using the enhanced quality scoring.

        Args:
            result: The result to calculate a quality score for

        Returns:
            A quality score between 0 and 1
        """
        return calculate_enhanced_quality_score(result)

    def get_phase_metrics(self, phase: Optional[Phase] = None) -> Dict[str, Any]:
        """
        Get the metrics for a specific phase or the current phase.

        Args:
            phase: The phase to get metrics for, or None for the current phase

        Returns:
            The metrics for the specified phase
        """
        if phase is None:
            phase = self.current_phase

        if phase is None:
            return {}

        return self.phase_metrics.get_phase_metrics(phase)

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all metrics for all phases.

        Returns:
            A dictionary mapping phase names to phase metrics
        """
        return self.phase_metrics.get_all_metrics()

    def get_metrics_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of phase transitions and metrics.

        Returns:
            A list of dictionaries containing phase transition history
        """
        return self.phase_metrics.get_history()

    def create_micro_cycle(
        self, task: Dict[str, Any], parent_phase: Phase
    ) -> "EnhancedEDRRCoordinator":
        """
        Create a micro-EDRR cycle within the current phase.

        This method overrides the parent implementation to create an EnhancedEDRRCoordinator
        instance instead of a regular EDRRCoordinator.

        Args:
            task: The task for the micro cycle
            parent_phase: The phase of the parent cycle that created this micro cycle

        Returns:
            A new EnhancedEDRRCoordinator instance representing the micro cycle

        Raises:
            EDRRCoordinatorError: If recursion depth limit is exceeded or delimiting principles
                                 prevent the creation of the micro cycle
        """
        # Check recursion depth limit
        if self.recursion_depth >= self.max_recursion_depth:
            error_msg = f"Maximum recursion depth ({self.max_recursion_depth}) exceeded"
            logger.error(error_msg)
            raise EDRRCoordinatorError(error_msg)

        # Check delimiting principles
        should_terminate, reason = self.should_terminate_recursion(task)
        if should_terminate:
            error_msg = f"Recursion terminated due to {reason}"
            logger.error(error_msg)
            raise EDRRCoordinatorError(error_msg)

        # Create a new EnhancedEDRRCoordinator instance for the micro cycle
        micro_cycle = EnhancedEDRRCoordinator(
            memory_manager=self.memory_manager,
            wsde_team=self.wsde_team,
            code_analyzer=self.code_analyzer,
            ast_transformer=self.ast_transformer,
            prompt_manager=self.prompt_manager,
            documentation_manager=self.documentation_manager,
            enable_enhanced_logging=self._enable_enhanced_logging,
            parent_cycle_id=self.cycle_id,
            recursion_depth=self.recursion_depth + 1,
            parent_phase=parent_phase,
            config=self.config,
        )

        # Start the micro cycle
        micro_cycle.start_cycle(task)

        # Return the micro cycle
        return micro_cycle

    def _get_llm_response(self, prompt: str, system_prompt: str | None = None) -> str:
        """Return an LLM completion for ``prompt`` using the provider system."""
        from devsynth.adapters.provider_system import complete

        try:
            return complete(prompt=prompt, system_prompt=system_prompt)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("LLM request failed: %s", exc)
            return ""

    def execute_single_agent_task(
        self,
        task: Dict[str, Any],
        agent_name: str,
        phase: Phase,
        llm_prompt: str | None = None,
    ) -> Dict[str, Any]:
        """Execute ``task`` with a specific agent and store results."""

        agent = self.wsde_team.get_agent(agent_name)
        if agent is None:
            raise EDRRCoordinatorError(f"Agent {agent_name} not found")

        if llm_prompt:
            llm_response = self._get_llm_response(llm_prompt)
            self._safe_store_with_edrr_phase(
                llm_response,
                MemoryType.CONTEXT,
                phase.value,
                {
                    "cycle_id": self.cycle_id,
                    "agent": agent_name,
                    "type": "LLM_RESPONSE",
                },
            )

        result = agent.process(task)

        quality_score = self._calculate_quality_score(result)
        if isinstance(result, dict):
            result["quality_score"] = quality_score

        self._safe_store_with_edrr_phase(
            result,
            MemoryType.EPISODIC,
            phase.value,
            {"cycle_id": self.cycle_id, "agent": agent_name, "type": "TASK_RESULT"},
        )

        return result
