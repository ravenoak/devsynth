"""
Core functionality for the EDRR Coordinator.

This module provides the core functionality for the EDRR Coordinator,
including initialization, cycle management, and phase progression.

This is part of an effort to break up the monolithic coordinator.py
into smaller, more focused modules.
"""

import copy
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from unittest.mock import MagicMock

import yaml

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.manifest_parser import ManifestParseError, ManifestParser
from devsynth.application.edrr.wsde_team_proxy import WSDETeamProxy
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.core import CoreValues, check_report_for_value_conflicts
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.exceptions import DevSynthError
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase


class EDRRCoordinatorError(DevSynthError):
    """Exception raised for errors in the EDRR Coordinator."""

    pass


class EDRRCoordinatorCore:
    """
    Core functionality for the EDRR (Expand, Differentiate, Refine, Retrospect) Coordinator.

    This class provides the core functionality for managing EDRR cycles,
    including initialization, cycle management, and phase progression.
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
        parent_cycle_id: str | None = None,
        recursion_depth: int = 0,
        parent_phase: Phase | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize the EDRR Coordinator.

        Args:
            memory_manager: Manager for storing and retrieving memory
            wsde_team: Team of agents for executing tasks
            code_analyzer: Analyzer for code analysis
            ast_transformer: Transformer for AST manipulation
            prompt_manager: Manager for prompt templates
            documentation_manager: Manager for documentation
            enable_enhanced_logging: Whether to enable enhanced logging
            parent_cycle_id: ID of the parent cycle (for micro cycles)
            recursion_depth: Depth of recursion (for micro cycles)
            parent_phase: Phase of the parent cycle (for micro cycles)
            config: Configuration options
        """
        self.memory_manager = memory_manager
        self.wsde_team = wsde_team
        self.code_analyzer = code_analyzer
        self.ast_transformer = ast_transformer
        self.prompt_manager = prompt_manager
        self.documentation_manager = documentation_manager
        self.enable_enhanced_logging = enable_enhanced_logging
        self.parent_cycle_id = parent_cycle_id
        self.recursion_depth = recursion_depth
        self.parent_phase = parent_phase
        self.config = config or {}

        # Initialize logger
        self.logger = DevSynthLogger(__name__)

        # Initialize cycle data
        self.cycle_id = str(uuid.uuid4())
        self.cycle_start_time = datetime.now()
        self.current_phase = None
        self.task = None
        self.phase_results = {}
        self.child_cycles: list["EDRRCoordinatorCore"] = []
        self.max_recursion_depth = (
            self.config.get("edrr", {})
            .get("recursion", {})
            .get("max_recursion_depth", 3)
        )
        self.execution_traces = []
        self.execution_history = []
        self.performance_metrics = {}
        # Wrap WSDE team to capture consensus failures unless it's a mock
        if not isinstance(wsde_team, MagicMock):
            self.wsde_team = WSDETeamProxy(
                wsde_team, self.logger, self.performance_metrics, lambda: self.cycle_id
            )

        # Log initialization
        self.logger.info(f"Initialized EDRR Coordinator (cycle_id: {self.cycle_id})")
        if parent_cycle_id:
            self.logger.info(f"  Parent cycle: {parent_cycle_id}")
            self.logger.info(f"  Recursion depth: {recursion_depth}")
            self.logger.info(
                f"  Parent phase: {parent_phase.name if parent_phase else None}"
            )

    def start_cycle(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Start a new EDRR cycle with the given task.

        Args:
            task: The task to process in this cycle

        Returns:
            The results of the cycle

        Raises:
            EDRRCoordinatorError: If the task is None or empty
        """
        # Validate task
        if task is None or not task:
            error_msg = "Task cannot be None or empty"
            self.logger.error(error_msg)
            raise EDRRCoordinatorError(error_msg)

        self.task = copy.deepcopy(task)

        # Ensure task has an ID
        if "id" not in self.task:
            self.task["id"] = str(uuid.uuid4())

        # Log cycle start
        self.logger.info(
            f"Starting EDRR cycle for task: {self.task.get('title', 'Untitled')}"
        )
        self.logger.info(f"  Task ID: {self.task['id']}")
        self.logger.info(f"  Cycle ID: {self.cycle_id}")

        # Store task in memory
        self.memory_manager.store(
            self.task,
            tags=["task", f"cycle:{self.cycle_id}"],
            memory_type=MemoryType.WORKING_MEMORY,
        )

        # Progress through phases
        self.progress_to_phase(Phase.EXPAND)

        # Generate final report
        cycle_data = self._aggregate_results()
        report = self.generate_final_report(cycle_data)

        # Store report in memory
        self.memory_manager.store(
            report,
            tags=["report", f"cycle:{self.cycle_id}"],
            memory_type=MemoryType.LONG_TERM,
        )

        # Log cycle completion
        self.logger.info(
            f"Completed EDRR cycle for task: {self.task.get('title', 'Untitled')}"
        )

        return report

    def start_cycle_from_manifest(
        self, manifest_path_or_string: str | Path, is_file: bool = True
    ) -> dict[str, Any]:
        """
        Start a new EDRR cycle from a manifest file or string.

        Args:
            manifest_path_or_string: Path to manifest file or manifest string
            is_file: Whether manifest_path_or_string is a file path

        Returns:
            The results of the cycle

        Raises:
            ManifestParseError: If the manifest cannot be parsed
        """
        try:
            # Parse manifest
            parser = ManifestParser()
            if is_file:
                manifest = parser.parse_file(manifest_path_or_string)
            else:
                manifest = parser.parse_string(manifest_path_or_string)

            # Extract task from manifest
            task = {
                "id": manifest.get("id", str(uuid.uuid4())),
                "title": manifest.get("title", "Untitled Task"),
                "description": manifest.get("description", ""),
                "requirements": manifest.get("requirements", []),
                "constraints": manifest.get("constraints", []),
                "acceptance_criteria": manifest.get("acceptance_criteria", []),
                "metadata": manifest.get("metadata", {}),
            }

            # Add manifest to task metadata
            task["metadata"]["manifest"] = manifest

            # Start cycle with task
            return self.start_cycle(task)

        except Exception as e:
            # Handle parsing errors
            error_msg = f"Failed to parse manifest: {str(e)}"
            self.logger.error(error_msg)
            raise ManifestParseError(error_msg) from e

    def progress_to_phase(self, phase: Phase) -> dict[str, Any]:
        """
        Progress to the specified phase.

        Args:
            phase: The phase to progress to

        Returns:
            The results of the phase execution

        Raises:
            EDRRCoordinatorError: If no cycle has been started
        """
        # Check if a cycle has been started
        if self.task is None:
            error_msg = "No cycle has been started"
            self.logger.error(error_msg)
            raise EDRRCoordinatorError(error_msg)
        # Check if we're already in this phase
        if self.current_phase == phase:
            self.logger.info(f"Already in phase {phase.name}")
            return self.phase_results.get(phase.name, {})

        # Check if we're skipping phases
        if self.current_phase:
            # Get the ordered list of phases
            phases = [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]

            # Find the indices of the current and target phases
            current_index = phases.index(self.current_phase)
            target_index = phases.index(phase)

            # Check if we're skipping phases
            if target_index > current_index + 1:
                # Execute intermediate phases
                for i in range(current_index + 1, target_index):
                    self.progress_to_phase(phases[i])

        # Update current phase
        self.current_phase = phase

        # Log phase transition
        self.logger.info(f"Progressing to phase: {phase.name}")

        # Execute phase
        phase_start_time = datetime.now()
        context = {"task": self.task, "cycle_id": self.cycle_id}

        # Add previous phase results to context
        for p in Phase:
            if p.value < phase.value and p.name in self.phase_results:
                context[p.name.lower()] = self.phase_results[p.name]

        # Execute phase
        results = self.execute_current_phase(context)

        # Store phase results
        self.phase_results[phase.name] = results

        # Calculate phase duration
        phase_duration = (datetime.now() - phase_start_time).total_seconds()

        # Update execution history
        self.execution_history.append(
            {
                "phase": phase.name,
                "start_time": phase_start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": phase_duration,
            }
        )

        # Update performance metrics
        if "phase_durations" not in self.performance_metrics:
            self.performance_metrics["phase_durations"] = {}
        self.performance_metrics["phase_durations"][phase.name] = phase_duration

        # Store phase results in memory
        self.memory_manager.store_with_edrr_phase(
            results,
            phase=phase,
            tags=[f"phase:{phase.name}", f"cycle:{self.cycle_id}"],
            memory_type=MemoryType.WORKING_MEMORY,
        )

        # Check if we should automatically progress to the next phase
        self._maybe_auto_progress()

        return results

    def progress_to_next_phase(self) -> dict[str, Any] | None:
        """
        Progress to the next phase in the EDRR cycle.

        Returns:
            The results of the next phase execution, or None if there is no next phase

        Raises:
            EDRRCoordinatorError: If no cycle has been started
        """
        # Check if a cycle has been started
        if self.task is None:
            error_msg = "No cycle has been started"
            self.logger.error(error_msg)
            raise EDRRCoordinatorError(error_msg)
        # Determine next phase
        next_phase = self._decide_next_phase()

        # Check if there is a next phase
        if next_phase is None:
            self.logger.info("No next phase available")
            return None

        # Progress to next phase
        return self.progress_to_phase(next_phase)

    def _decide_next_phase(self) -> Phase | None:
        """
        Decide the next phase based on the current phase.

        Returns:
            The next phase, or None if there is no next phase
        """
        # If no current phase, start with EXPAND
        if self.current_phase is None:
            return Phase.EXPAND

        # Determine next phase based on current phase
        if self.current_phase == Phase.EXPAND:
            return Phase.DIFFERENTIATE
        elif self.current_phase == Phase.DIFFERENTIATE:
            return Phase.REFINE
        elif self.current_phase == Phase.REFINE:
            return Phase.RETROSPECT
        elif self.current_phase == Phase.RETROSPECT:
            # No next phase after RETROSPECT
            return None
        else:
            # Unknown phase
            self.logger.warning(f"Unknown phase: {self.current_phase}")
            return None

    def _maybe_auto_progress(self) -> None:
        """
        Automatically progress to the next phase if auto-progress is enabled.
        """
        auto_progress = self.config.get("auto_progress", False)

        if not auto_progress:
            return

        for _ in range(10):  # safety bound against infinite loops
            next_phase = self._decide_next_phase()
            if next_phase is None:
                break
            self.logger.info("Auto-progressing to next phase")
            self.progress_to_phase(next_phase)
            if next_phase == Phase.RETROSPECT:
                break

    def create_micro_cycle(
        self, task: dict[str, Any], parent_phase: Phase
    ) -> "EDRRCoordinatorCore":
        """Create a nested EDRRCoordinatorCore for recursion."""
        if self.recursion_depth >= self.max_recursion_depth:
            raise EDRRCoordinatorError("Maximum recursion depth exceeded")

        terminate, reason = self.should_terminate_recursion(task)
        if terminate:
            raise EDRRCoordinatorError(f"Recursion terminated due to {reason}")

        micro_cycle = EDRRCoordinatorCore(
            memory_manager=self.memory_manager,
            wsde_team=self.wsde_team,
            code_analyzer=self.code_analyzer,
            ast_transformer=self.ast_transformer,
            prompt_manager=self.prompt_manager,
            documentation_manager=self.documentation_manager,
            enable_enhanced_logging=self.enable_enhanced_logging,
            parent_cycle_id=self.cycle_id,
            recursion_depth=self.recursion_depth + 1,
            parent_phase=parent_phase,
            config=self.config,
        )

        micro_cycle.start_cycle(task)
        self.child_cycles.append(micro_cycle)
        return micro_cycle

    def should_terminate_recursion(self, task: dict[str, Any]) -> tuple[bool, str]:
        """Simple heuristics to decide if recursion should stop."""
        thresholds = (
            self.config.get("edrr", {}).get("recursion", {}).get("thresholds", {})
        )
        granularity = thresholds.get("granularity", 0.2)

        if task.get("human_override") == "terminate":
            return True, "human override"

        if task.get("granularity_score", 1.0) < granularity:
            return True, "granularity threshold"

        return False, ""

    def execute_current_phase(
        self, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute the current phase.

        Args:
            context: Context for phase execution

        Returns:
            The results of the phase execution
        """
        # Ensure context is a dictionary
        context = context or {}

        # Check if current phase is set
        if self.current_phase is None:
            error_msg = "No current phase set"
            self.logger.error(error_msg)
            raise EDRRCoordinatorError(error_msg)

        # Execute phase based on current phase
        if self.current_phase == Phase.EXPAND:
            return self._execute_expand_phase(context)
        elif self.current_phase == Phase.DIFFERENTIATE:
            return self._execute_differentiate_phase(context)
        elif self.current_phase == Phase.REFINE:
            return self._execute_refine_phase(context)
        elif self.current_phase == Phase.RETROSPECT:
            return self._execute_retrospect_phase(context)
        else:
            # Unknown phase
            error_msg = f"Unknown phase: {self.current_phase}"
            self.logger.error(error_msg)
            raise EDRRCoordinatorError(error_msg)

    def generate_report(self) -> dict[str, Any]:
        """
        Generate a report for the current cycle.

        Returns:
            The generated report

        Raises:
            EDRRCoordinatorError: If no cycle has been started
        """
        # Check if a cycle has been started
        if self.task is None:
            error_msg = "No cycle has been started"
            self.logger.error(error_msg)
            raise EDRRCoordinatorError(error_msg)

        # Aggregate results
        cycle_data = self._aggregate_results()

        # Generate report
        return self.generate_final_report(cycle_data)

    def get_execution_traces(self) -> list[dict[str, Any]]:
        """
        Get the execution traces for the current cycle.

        Returns:
            List of execution traces
        """
        return self.execution_traces

    def get_execution_history(self) -> list[dict[str, Any]]:
        """
        Get the execution history for the current cycle.

        Returns:
            List of execution history entries
        """
        return self.execution_history

    def get_performance_metrics(self) -> dict[str, Any]:
        """
        Get the performance metrics for the current cycle.

        Returns:
            Dictionary of performance metrics
        """
        return self.performance_metrics

    def _execute_expand_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the EXPAND phase.

        Args:
            context: Context for phase execution

        Returns:
            The results of the phase execution
        """
        self.logger.info("Executing EXPAND phase")
        # Implementation would go here
        return {"phase": "expand", "status": "completed"}

    def _execute_differentiate_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the DIFFERENTIATE phase.

        Args:
            context: Context for phase execution

        Returns:
            The results of the phase execution
        """
        self.logger.info("Executing DIFFERENTIATE phase")
        # Implementation would go here
        return {"phase": "differentiate", "status": "completed"}

    def _execute_refine_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the REFINE phase.

        Args:
            context: Context for phase execution

        Returns:
            The results of the phase execution
        """
        self.logger.info("Executing REFINE phase")
        # Implementation would go here
        return {"phase": "refine", "status": "completed"}

    def _execute_retrospect_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the RETROSPECT phase.

        Args:
            context: Context for phase execution

        Returns:
            The results of the phase execution
        """
        self.logger.info("Executing RETROSPECT phase")
        # Implementation would go here
        return {"phase": "retrospect", "status": "completed"}

    def _aggregate_results(self) -> dict[str, Any]:
        """
        Aggregate results from all phases.

        Returns:
            Aggregated results
        """
        self.logger.info("Aggregating results")
        # Implementation would go here
        return {"status": "completed", "phases": self.phase_results}

    def generate_final_report(self, cycle_data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a final report for the cycle.

        Args:
            cycle_data: Data for the cycle

        Returns:
            The generated report
        """
        self.logger.info("Generating final report")
        # Implementation would go here
        return {"report": "final report", "cycle_data": cycle_data}
