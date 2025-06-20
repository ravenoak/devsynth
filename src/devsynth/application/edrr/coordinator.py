"""EDRR Coordinator module.

This module defines the EDRRCoordinator class that orchestrates the flow between
components according to the EDRR (Expand, Differentiate, Refine, Retrospect) pattern.

The coordinator supports recursive EDRR cycles, where each macro phase can contain
its own nested micro-EDRR cycles, creating a fractal structure that enables
self-optimization at multiple levels of granularity.
"""

import copy
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import yaml

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.manifest_parser import ManifestParseError, ManifestParser
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.exceptions import DevSynthError
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Load default configuration for feature flags
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "default.yml"
try:
    with open(_DEFAULT_CONFIG_PATH, "r") as f:
        _DEFAULT_CONFIG = yaml.safe_load(f) or {}
except Exception:
    _DEFAULT_CONFIG = {}


class EDRRCoordinatorError(DevSynthError):
    """Error raised when the EDRR coordinator encounters an error."""

    pass


class EDRRCoordinator:
    """
    Coordinates the flow between components according to the EDRR pattern.

    This class orchestrates the interaction between the memory system, WSDE team,
    AST analyzer, prompt manager, and documentation manager to implement the
    EDRR (Expand, Differentiate, Refine, Retrospect) workflow.

    It can be driven by an EDRR manifest, which provides instructions, templates,
    and resources for each phase of the EDRR process.

    The coordinator supports recursive EDRR cycles, where each macro phase can contain
    its own nested micro-EDRR cycles, creating a fractal structure that enables
    self-optimization at multiple levels of granularity.
    """

    # Default maximum recursion depth to prevent infinite recursion
    DEFAULT_MAX_RECURSION_DEPTH = 3

    # Default thresholds for delimiting principles
    DEFAULT_GRANULARITY_THRESHOLD = 0.2
    DEFAULT_COST_BENEFIT_RATIO = 0.5
    DEFAULT_QUALITY_THRESHOLD = 0.9
    DEFAULT_RESOURCE_LIMIT = 0.8

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
        Initialize the EDRR coordinator.

        Args:
            memory_manager: The memory manager to use
            wsde_team: The WSDE team to coordinate
            code_analyzer: The code analyzer to use
            ast_transformer: The AST transformer to use
            prompt_manager: The prompt manager to use
            documentation_manager: The documentation manager to use
            enable_enhanced_logging: Whether to enable enhanced logging
            parent_cycle_id: The ID of the parent cycle (for micro cycles)
            recursion_depth: The recursion depth of this cycle (0 for macro cycles)
            parent_phase: The phase of the parent cycle that created this micro cycle
        """
        self.memory_manager = memory_manager
        self.wsde_team = wsde_team
        self.code_analyzer = code_analyzer
        self.ast_transformer = ast_transformer
        self.prompt_manager = prompt_manager
        self.documentation_manager = documentation_manager
        self.config = config or _DEFAULT_CONFIG
        edrr_cfg = self.config.get("edrr", {})
        pt_cfg = edrr_cfg.get("phase_transition", {})
        feature_cfg = self.config.get("features", {})

        self.auto_phase_transitions = feature_cfg.get(
            "automatic_phase_transitions", pt_cfg.get("auto", True)
        )
        self.phase_transition_timeout = pt_cfg.get("timeout", 600)
        self._enable_enhanced_logging = enable_enhanced_logging
        self._execution_traces = {} if enable_enhanced_logging else None
        self._execution_history = [] if enable_enhanced_logging else None
        self.performance_metrics: Dict[str, Any] = {}

        self._phase_start_times: Dict[Phase, datetime] = {}

        # Recursive EDRR attributes
        self.parent_cycle_id = parent_cycle_id
        self.recursion_depth = recursion_depth
        self.parent_phase = parent_phase
        self.child_cycles = []
        self.max_recursion_depth = edrr_cfg.get(
            "max_recursion_depth", self.DEFAULT_MAX_RECURSION_DEPTH
        )

        self.manifest_parser = ManifestParser()
        self._manifest_parser = None
        self.current_phase = None
        self.task = None
        self.results = {}
        self.cycle_id = None
        self.manifest = None

        logger.info(
            f"EDRR coordinator initialized (recursion depth: {recursion_depth})"
        )

    def start_cycle(self, task: Dict[str, Any]) -> None:
        """Start a new EDRR cycle with the given task.

        Args:
            task: The task to process

        Example:
            >>> coordinator.start_cycle({"description": "Implement feature"})
        """
        self.task = task
        self.cycle_id = str(uuid.uuid4())
        self.results = {}
        self.manifest = None

        if self._enable_enhanced_logging:
            self._execution_traces = {
                "cycle_id": self.cycle_id,
                "phases": {},
                "metadata": {
                    "task_id": self.task.get("id"),
                    "task_description": self.task.get("description"),
                    "timestamp": datetime.now().isoformat(),
                },
            }
            self._execution_history = []

        # Store the task in memory
        self.memory_manager.store_with_edrr_phase(
            self.task, "TASK", "EXPAND", {"cycle_id": self.cycle_id}
        )

        # Initial role assignment before the first phase using dynamic roles
        self.wsde_team.assign_roles_for_phase(Phase.EXPAND, self.task)
        self.memory_manager.store_with_edrr_phase(
            self.wsde_team.get_role_map(),
            "ROLE_ASSIGNMENT",
            Phase.EXPAND.value,
            {"cycle_id": self.cycle_id},
        )

        # Enter the Expand phase
        self.progress_to_phase(Phase.EXPAND)

        logger.info(
            f"Started EDRR cycle for task: {task.get('description', 'Unknown')}"
        )

    def start_cycle_from_manifest(
        self, manifest_path_or_string: Union[str, Path], is_file: bool = True
    ) -> None:
        """
        Start a new EDRR cycle using a manifest.

        Args:
            manifest_path_or_string: The path to the manifest file or the manifest as a string
            is_file: Whether manifest_path_or_string is a file path (True) or a string (False)

        Raises:
            EDRRCoordinatorError: If the manifest cannot be parsed

        Example:
            >>> coordinator.start_cycle_from_manifest("manifest.json")
        """
        try:
            # Disable automatic phase transitions during manifest-driven runs
            self.auto_phase_transitions = False
            # Parse the manifest
            if is_file:
                self.manifest = self.manifest_parser.parse_file(manifest_path_or_string)
            else:
                self.manifest = self.manifest_parser.parse_string(
                    manifest_path_or_string
                )

            # Start execution tracking
            self.manifest_parser.start_execution()

            # Create a task from the manifest
            self.task = {
                "id": self.manifest_parser.get_manifest_id(),
                "description": self.manifest_parser.get_manifest_description(),
                "metadata": self.manifest_parser.get_manifest_metadata(),
            }

            self.cycle_id = str(uuid.uuid4())
            self.results = {}

            if self._enable_enhanced_logging:
                self._execution_traces = {
                    "cycle_id": self.cycle_id,
                    "phases": {},
                    "metadata": {
                        "task_id": self.task.get("id"),
                        "task_description": self.task.get("description"),
                        "timestamp": datetime.now().isoformat(),
                    },
                }
                self._execution_history = []

            # Store the task and manifest in memory with enhanced traceability
            self.memory_manager.store_with_edrr_phase(
                self.task,
                "TASK",
                Phase.EXPAND.value,
                metadata={
                    "cycle_id": self.cycle_id,
                    "from_manifest": True,
                    "manifest_id": self.manifest_parser.get_manifest_id(),
                    "execution_start_time": self.manifest_parser.execution_trace[
                        "start_time"
                    ],
                },
            )

            self.memory_manager.store_with_edrr_phase(
                self.manifest,
                "MANIFEST",
                Phase.EXPAND.value,
                metadata={
                    "cycle_id": self.cycle_id,
                    "execution_trace_id": self.manifest_parser.execution_trace.get(
                        "manifest_id"
                    ),
                },
            )

            # Initial role assignment before the first phase using dynamic roles
            self.wsde_team.assign_roles_for_phase(Phase.EXPAND, self.task)
            self.memory_manager.store_with_edrr_phase(
                self.wsde_team.get_role_map(),
                "ROLE_ASSIGNMENT",
                Phase.EXPAND.value,
                {"cycle_id": self.cycle_id},
            )

            # Enter the Expand phase
            self.progress_to_phase(Phase.EXPAND)

            logger.info(
                f"Started EDRR cycle from manifest with ID: {self.task['id']} with enhanced traceability"
            )
        except ManifestParseError as e:
            logger.error(f"Failed to start cycle from manifest: {e}")
            raise EDRRCoordinatorError(f"Failed to start cycle from manifest: {e}")

    def progress_to_phase(self, phase: Phase) -> None:
        """
        Progress to the specified phase.

        Args:
            phase: The phase to progress to

        Raises:
            EDRRCoordinatorError: If the phase dependencies are not met

        Example:
            >>> coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        """
        try:
            # Check if using a manifest and if so, check phase dependencies
            if self.manifest is not None and self.manifest_parser:
                # Check if dependencies are met
                if not self.manifest_parser.check_phase_dependencies(phase):
                    error_msg = (
                        f"Cannot progress to {phase.value} phase: dependencies not met"
                    )
                    logger.error(error_msg)
                    raise EDRRCoordinatorError(error_msg)

                # Start tracking the phase
                self.manifest_parser.start_phase(phase)

            # Rotate Primus after the first phase
            previous_phase = self.current_phase
            if previous_phase is not None:
                self.wsde_team.rotate_primus()

            # Dynamic role assignment for the new phase
            self.wsde_team.assign_roles_for_phase(phase, self.task)
            self.memory_manager.store_with_edrr_phase(
                self.wsde_team.get_role_map(),
                "ROLE_ASSIGNMENT",
                phase.value,
                {"cycle_id": self.cycle_id},
            )

            # Store the phase transition in memory
            self.memory_manager.store_with_edrr_phase(
                {
                    "from": previous_phase.value if previous_phase else None,
                    "to": phase.value,
                },
                "PHASE_TRANSITION",
                phase.value,
                {"cycle_id": self.cycle_id},
            )

            # Update the current phase
            self.current_phase = phase

            start_time = datetime.now()
            self._phase_start_times[phase] = start_time
            if self._enable_enhanced_logging:
                self._execution_history.append(
                    {
                        "timestamp": start_time.isoformat(),
                        "phase": phase.value,
                        "action": "start",
                        "details": {},
                    }
                )

            # Execute the phase
            if phase == Phase.EXPAND:
                results = self._execute_expand_phase({})
            elif phase == Phase.DIFFERENTIATE:
                results = self._execute_differentiate_phase({})
            elif phase == Phase.REFINE:
                results = self._execute_refine_phase({})
            elif phase == Phase.RETROSPECT:
                results = self._execute_retrospect_phase({})

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self.performance_metrics[phase.name] = {
                "duration": duration,
                "memory_usage": len(str(results)),
                "component_calls": {
                    "wsde_team": 1,
                    "code_analyzer": 1,
                    "prompt_manager": 1,
                    "documentation_manager": 1,
                },
            }

            if self._enable_enhanced_logging:
                self._execution_history.append(
                    {
                        "timestamp": end_time.isoformat(),
                        "phase": phase.value,
                        "action": "end",
                        "details": {"duration": duration},
                    }
                )

            # Save results
            self.results[phase.name] = results
            # Refresh aggregated results
            self._aggregate_results()

            # Complete tracking the phase if using a manifest
            if self.manifest is not None and self.manifest_parser:
                self.manifest_parser.complete_phase(phase, self.results.get(phase))

            logger.info(
                f"Progressed to and completed {phase.value} phase for task: {self.task.get('description', 'Unknown')}"
            )

            # Automatically transition to next phase if enabled
            self._maybe_auto_progress()
        except ManifestParseError as e:
            logger.error(f"Failed to progress to phase {phase.value}: {e}")
            raise EDRRCoordinatorError(
                f"Failed to progress to phase {phase.value}: {e}"
            )

    def progress_to_next_phase(self) -> None:
        """Progress to the next phase in the standard EDRR sequence.

        Example:
            >>> coordinator.current_phase = Phase.EXPAND
            >>> coordinator.progress_to_next_phase()
        """
        if self.current_phase is None:
            raise EDRRCoordinatorError("No current phase set")

        phase_order = [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]
        try:
            idx = phase_order.index(self.current_phase)
        except ValueError as exc:
            raise EDRRCoordinatorError("Unknown current phase") from exc

        if idx >= len(phase_order) - 1:
            raise EDRRCoordinatorError("Already at final phase")

        next_phase = phase_order[idx + 1]
        self.progress_to_phase(next_phase)

    def _decide_next_phase(self) -> Optional[Phase]:
        """Determine if the coordinator should automatically move to the next phase."""
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

        phase_results = self.results.get(self.current_phase.name, {})
        if phase_results.get("phase_complete", False) is True:
            return next_phase

        start_time = self._phase_start_times.get(self.current_phase)
        if (
            start_time
            and (datetime.now() - start_time).total_seconds()
            >= self.phase_transition_timeout
        ):
            return next_phase

        return None

    def _maybe_auto_progress(self) -> None:
        """Trigger automatic phase transition when conditions are met."""
        if not self.auto_phase_transitions or not hasattr(
            self.wsde_team, "elaborate_details"
        ):
            return
        while True:
            next_phase = self._decide_next_phase()
            if not next_phase:
                break
            self.progress_to_phase(next_phase)

    def create_micro_cycle(
        self, task: Dict[str, Any], parent_phase: Phase
    ) -> "EDRRCoordinator":
        """
        Create a micro-EDRR cycle within the current phase.

        This method creates a new EDRRCoordinator instance that represents a micro-EDRR cycle
        within the current phase. The micro cycle inherits the dependencies from the parent
        cycle but has its own task, cycle ID, and results.

        Args:
            task: The task for the micro cycle
            parent_phase: The phase of the parent cycle that created this micro cycle

        Returns:
            A new EDRRCoordinator instance representing the micro cycle

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
        if self.should_terminate_recursion(task):
            error_msg = "Recursion terminated based on delimiting principles"
            logger.error(error_msg)
            raise EDRRCoordinatorError(error_msg)

        # Create a new EDRRCoordinator instance for the micro cycle
        micro_cycle = EDRRCoordinator(
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
        )

        # Start the micro cycle with the given task or manifest
        if isinstance(task, dict) and "manifest" in task:
            manifest = task["manifest"]
            if isinstance(manifest, (str, Path)):
                micro_cycle.start_cycle_from_manifest(manifest, is_file=True)
            else:
                micro_cycle.start_cycle_from_manifest(
                    json.dumps(manifest), is_file=False
                )
        else:
            micro_cycle.start_cycle(task)

        # Add the micro cycle to the list of child cycles
        self.child_cycles.append(micro_cycle)

        # Store the micro cycle in memory
        self.memory_manager.store_with_edrr_phase(
            {"micro_cycle_id": micro_cycle.cycle_id, "task": task},
            "MICRO_CYCLE",
            parent_phase.value,
            {"cycle_id": self.cycle_id, "recursion_depth": self.recursion_depth + 1},
        )

        # Initialize micro_cycle_results in the parent phase results if it doesn't exist
        if parent_phase not in self.results:
            self.results[parent_phase] = {}
        if "micro_cycle_results" not in self.results[parent_phase]:
            self.results[parent_phase]["micro_cycle_results"] = {}

        # Add a placeholder for the micro cycle results
        self.results[parent_phase]["micro_cycle_results"][micro_cycle.cycle_id] = {
            **micro_cycle.results,
            "task": task,
        }

        self._aggregate_results()

        logger.info(
            f"Created micro-EDRR cycle with ID {micro_cycle.cycle_id} at recursion depth {micro_cycle.recursion_depth}"
        )
        return micro_cycle

    def should_terminate_recursion(self, task: Dict[str, Any]) -> bool:
        """
        Determine whether recursion should be terminated based on delimiting principles.

        Args:
            task: The task for the potential micro cycle

        Returns:
            True if recursion should be terminated, False otherwise
        """
        # Check for human override
        if "human_override" in task:
            if task["human_override"] == "terminate":
                logger.info("Recursion terminated due to human override")
                return True
            elif task["human_override"] == "continue":
                logger.info("Recursion continued due to human override")
                return False

        # Check granularity threshold
        if "granularity_score" in task:
            if task["granularity_score"] < self.DEFAULT_GRANULARITY_THRESHOLD:
                logger.info(
                    f"Recursion terminated due to granularity threshold: {task['granularity_score']} < {self.DEFAULT_GRANULARITY_THRESHOLD}"
                )
                return True

        # Check cost-benefit analysis
        if "cost_score" in task and "benefit_score" in task:
            cost_benefit_ratio = (
                task["cost_score"] / task["benefit_score"]
                if task["benefit_score"] > 0
                else float("inf")
            )
            if cost_benefit_ratio > self.DEFAULT_COST_BENEFIT_RATIO:
                logger.info(
                    f"Recursion terminated due to cost-benefit analysis: {cost_benefit_ratio} > {self.DEFAULT_COST_BENEFIT_RATIO}"
                )
                return True

        # Check quality threshold
        if "quality_score" in task:
            if task["quality_score"] > self.DEFAULT_QUALITY_THRESHOLD:
                logger.info(
                    f"Recursion terminated due to quality threshold: {task['quality_score']} > {self.DEFAULT_QUALITY_THRESHOLD}"
                )
                return True

        # Check resource limits
        if "resource_usage" in task:
            if task["resource_usage"] > self.DEFAULT_RESOURCE_LIMIT:
                logger.info(
                    f"Recursion terminated due to resource limit: {task['resource_usage']} > {self.DEFAULT_RESOURCE_LIMIT}"
                )
                return True

        # Default to allowing recursion
        return False

    def _maybe_create_micro_cycles(
        self, context: Dict[str, Any], parent_phase: Phase, results: Dict[str, Any]
    ) -> None:
        """Create micro cycles for tasks provided in the context."""
        micro_tasks = context.get("micro_tasks", []) if context else []
        if not micro_tasks:
            return

        if "micro_cycle_results" not in results:
            results["micro_cycle_results"] = {}

        for task in micro_tasks:
            try:
                micro_cycle = self.create_micro_cycle(task, parent_phase)
                results["micro_cycle_results"][
                    micro_cycle.cycle_id
                ] = micro_cycle.results
            except EDRRCoordinatorError as exc:
                results["micro_cycle_results"][task.get("description", "task")] = {
                    "error": str(exc)
                }

    def _execute_expand_phase(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the Expand phase of the EDRR cycle.

        This phase focuses on divergent thinking, broad exploration,
        idea generation, and knowledge retrieval optimization.

        Args:
            context: The context for the phase execution

        Returns:
            The results of the Expand phase
        """
        if context is None:
            context = {}

        logger.info(f"Executing Expand phase (recursion depth: {self.recursion_depth})")
        results = {}

        # Render phase-specific prompt if available
        expand_prompt = self.prompt_manager.render_prompt(
            "expand_phase", {"task_description": self.task.get("description", "")}
        )
        if expand_prompt:
            results["prompt"] = expand_prompt

        # Implement divergent thinking patterns
        broad_ideas = self.wsde_team.generate_diverse_ideas(
            self.task, max_ideas=10, diversity_threshold=0.7
        )
        results["ideas"] = broad_ideas

        # Perform knowledge retrieval optimization
        if hasattr(self.memory_manager, "retrieve_relevant_knowledge"):
            relevant_knowledge = self.memory_manager.retrieve_relevant_knowledge(
                self.task,
                retrieval_strategy="broad",
                max_results=15,
                similarity_threshold=0.6,
            )
        else:
            relevant_knowledge = []
        results["knowledge"] = relevant_knowledge

        # Execute broad exploration algorithms
        code_elements = self.code_analyzer.analyze_project_structure(
            exploration_depth="maximum",
            include_dependencies=True,
            extract_relationships=True,
        )
        results["code_elements"] = code_elements

        # Initialize micro_cycle_results if it doesn't exist
        if "micro_cycle_results" not in results:
            results["micro_cycle_results"] = {}

        # Store results in memory with phase tag
        self.memory_manager.store_with_edrr_phase(
            results,
            "EXPAND_RESULTS",
            "EXPAND",
            {"cycle_id": self.cycle_id, "recursion_depth": self.recursion_depth},
        )

        # Create micro cycles for any provided sub tasks
        self._maybe_create_micro_cycles(context, Phase.EXPAND, results)

        if self._enable_enhanced_logging:
            trace_data = {
                "timestamp": datetime.now().isoformat(),
                "inputs": context,
                "outputs": results,
                "metrics": {
                    "ideas_count": len(broad_ideas),
                    "knowledge_items": len(relevant_knowledge),
                    "code_elements": len(code_elements) if code_elements else 0,
                },
            }

            # Add recursive information if this is a micro cycle
            if self.recursion_depth > 0:
                trace_data["parent_cycle_id"] = self.parent_cycle_id
                trace_data["recursion_depth"] = self.recursion_depth
                trace_data["parent_phase"] = (
                    self.parent_phase.value if self.parent_phase else None
                )

            self._execution_traces[f"EXPAND_{self.cycle_id}"] = trace_data

        logger.info(
            f"Expand phase completed with {len(broad_ideas)} ideas generated (recursion depth: {self.recursion_depth})"
        )
        return results

    def _execute_differentiate_phase(
        self, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute the Differentiate phase of the EDRR cycle.

        This phase focuses on comparative analysis, option evaluation,
        trade-off analysis, and decision criteria formulation.

        Args:
            context: The context for the phase execution

        Returns:
            The results of the Differentiate phase
        """
        if context is None:
            context = {}

        logger.info(
            f"Executing Differentiate phase (recursion depth: {self.recursion_depth})"
        )
        results = {}

        diff_prompt = self.prompt_manager.render_prompt(
            "differentiate_phase",
            {"task_description": self.task.get("description", "")},
        )
        if diff_prompt:
            results["prompt"] = diff_prompt

        # Get ideas from the Expand phase
        if hasattr(self.memory_manager, "retrieve_with_edrr_phase"):
            expand_results = self.memory_manager.retrieve_with_edrr_phase(
                "EXPAND_RESULTS", "EXPAND", {"cycle_id": self.cycle_id}
            )
        else:
            expand_results = {}
        ideas = expand_results.get("ideas", [])

        # Implement comparative analysis frameworks
        comparison_matrix = self.wsde_team.create_comparison_matrix(
            ideas,
            evaluation_criteria=[
                "feasibility",
                "impact",
                "alignment_with_requirements",
                "implementation_complexity",
                "maintainability",
            ],
        )
        results["comparison_matrix"] = comparison_matrix

        # Add option evaluation metrics
        evaluated_options = self.wsde_team.evaluate_options(
            ideas,
            comparison_matrix,
            weighting_scheme={
                "feasibility": 0.25,
                "impact": 0.25,
                "alignment_with_requirements": 0.2,
                "implementation_complexity": 0.15,
                "maintainability": 0.15,
            },
        )
        results["evaluated_options"] = evaluated_options

        # Perform trade-off analysis
        trade_offs = self.wsde_team.analyze_trade_offs(
            evaluated_options,
            conflict_detection_threshold=0.7,
            identify_complementary_options=True,
        )
        results["trade_offs"] = trade_offs

        # Decision criteria formulation
        decision_criteria = self.wsde_team.formulate_decision_criteria(
            self.task,
            evaluated_options,
            trade_offs,
            contextualize_with_code=True,
            code_analyzer=self.code_analyzer,
        )
        results["decision_criteria"] = decision_criteria

        # Initialize micro_cycle_results if it doesn't exist
        if "micro_cycle_results" not in results:
            results["micro_cycle_results"] = {}

        # Store results in memory with phase tag
        self.memory_manager.store_with_edrr_phase(
            results,
            "DIFFERENTIATE_RESULTS",
            "DIFFERENTIATE",
            {"cycle_id": self.cycle_id, "recursion_depth": self.recursion_depth},
        )

        # Create micro cycles for any provided sub tasks
        self._maybe_create_micro_cycles(context, Phase.DIFFERENTIATE, results)

        if self._enable_enhanced_logging:
            trace_data = {
                "timestamp": datetime.now().isoformat(),
                "inputs": context,
                "outputs": results,
                "metrics": {
                    "ideas_evaluated": len(ideas),
                    "trade_offs_identified": len(trade_offs),
                    "decision_criteria": len(decision_criteria),
                },
            }

            # Add recursive information if this is a micro cycle
            if self.recursion_depth > 0:
                trace_data["parent_cycle_id"] = self.parent_cycle_id
                trace_data["recursion_depth"] = self.recursion_depth
                trace_data["parent_phase"] = (
                    self.parent_phase.value if self.parent_phase else None
                )

            self._execution_traces[f"DIFFERENTIATE_{self.cycle_id}"] = trace_data

        logger.info(
            f"Differentiate phase completed with {len(evaluated_options)} options evaluated (recursion depth: {self.recursion_depth})"
        )
        return results

    def _execute_refine_phase(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the Refine phase of the EDRR cycle.

        This phase focuses on detail elaboration, implementation planning,
        optimization algorithms, and quality assurance.

        Args:
            context: The context for the phase execution

        Returns:
            The results of the Refine phase
        """
        if context is None:
            context = {}

        logger.info(f"Executing Refine phase (recursion depth: {self.recursion_depth})")
        results = {}

        refine_prompt = self.prompt_manager.render_prompt(
            "refine_phase", {"task_description": self.task.get("description", "")}
        )
        if refine_prompt:
            results["prompt"] = refine_prompt

        # Get evaluated options from the Differentiate phase
        if hasattr(self.memory_manager, "retrieve_with_edrr_phase"):
            differentiate_results = self.memory_manager.retrieve_with_edrr_phase(
                "DIFFERENTIATE_RESULTS", "DIFFERENTIATE", {"cycle_id": self.cycle_id}
            )
        else:
            differentiate_results = {}
        evaluated_options = differentiate_results.get("evaluated_options", [])
        decision_criteria = differentiate_results.get("decision_criteria", {})

        # Select the best option based on decision criteria
        selected_option = self.wsde_team.select_best_option(
            evaluated_options, decision_criteria
        )
        results["selected_option"] = selected_option

        # Detail elaboration techniques
        try:
            detailed_plan = self.wsde_team.elaborate_details(
                selected_option,
                detail_level="high",
                include_edge_cases=True,
                consider_constraints=True,
            )
        except TypeError:
            detailed_plan = self.wsde_team.elaborate_details(selected_option)
        results["detailed_plan"] = detailed_plan

        # Implementation planning
        try:
            implementation_plan = self.wsde_team.create_implementation_plan(
                detailed_plan,
                code_analyzer=self.code_analyzer,
                ast_transformer=self.ast_transformer,
                include_testing_strategy=True,
            )
        except TypeError:
            implementation_plan = self.wsde_team.create_implementation_plan(
                detailed_plan
            )
        results["implementation_plan"] = implementation_plan

        # Optimization algorithms
        try:
            optimized_plan = self.wsde_team.optimize_implementation(
                implementation_plan,
                optimization_targets=["performance", "readability", "maintainability"],
                code_analyzer=self.code_analyzer,
            )
        except TypeError:
            optimized_plan = self.wsde_team.optimize_implementation(
                implementation_plan, []
            )
        results["optimized_plan"] = optimized_plan

        # Quality assurance checks
        try:
            quality_checks = self.wsde_team.perform_quality_assurance(
                optimized_plan,
                check_categories=[
                    "security",
                    "performance",
                    "maintainability",
                    "testability",
                ],
                code_analyzer=self.code_analyzer,
            )
        except TypeError:
            quality_checks = self.wsde_team.perform_quality_assurance(optimized_plan)
        results["quality_checks"] = quality_checks

        # Optional peer review of the optimized plan
        reviewers = (
            context.get("peer_review", {}).get("reviewers", []) if context else []
        )
        if reviewers:
            author = self.wsde_team.get_primus()
            pr_result = self.wsde_team.conduct_peer_review(
                optimized_plan, author, reviewers
            )
            results["peer_review"] = pr_result
            self.memory_manager.store_with_edrr_phase(
                pr_result,
                "PEER_REVIEW_RESULTS",
                "REFINE",
                {"cycle_id": self.cycle_id, "recursion_depth": self.recursion_depth},
            )

        # Initialize micro_cycle_results if it doesn't exist
        if "micro_cycle_results" not in results:
            results["micro_cycle_results"] = {}

        # Store results in memory with phase tag
        self.memory_manager.store_with_edrr_phase(
            results,
            "REFINE_RESULTS",
            "REFINE",
            {"cycle_id": self.cycle_id, "recursion_depth": self.recursion_depth},
        )

        # Create micro cycles for any provided sub tasks
        self._maybe_create_micro_cycles(context, Phase.REFINE, results)

        if self._enable_enhanced_logging:
            trace_data = {
                "timestamp": datetime.now().isoformat(),
                "inputs": context,
                "outputs": results,
                "metrics": {
                    "plan_details_count": len(detailed_plan),
                    "implementation_steps": len(implementation_plan),
                    "quality_issues": len(quality_checks),
                },
            }

            # Add recursive information if this is a micro cycle
            if self.recursion_depth > 0:
                trace_data["parent_cycle_id"] = self.parent_cycle_id
                trace_data["recursion_depth"] = self.recursion_depth
                trace_data["parent_phase"] = (
                    self.parent_phase.value if self.parent_phase else None
                )

            self._execution_traces[f"REFINE_{self.cycle_id}"] = trace_data

        logger.info(
            f"Refine phase completed with implementation plan created (recursion depth: {self.recursion_depth})"
        )
        return results

    def _execute_retrospect_phase(
        self, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute the Retrospect phase of the EDRR cycle.

        This phase focuses on learning extraction, pattern recognition,
        knowledge integration, and improvement suggestion generation.

        Args:
            context: The context for the phase execution

        Returns:
            The results of the Retrospect phase
        """
        if context is None:
            context = {}

        logger.info(
            f"Executing Retrospect phase (recursion depth: {self.recursion_depth})"
        )
        results = {}

        retro_prompt = self.prompt_manager.render_prompt(
            "retrospect_phase", {"task_description": self.task.get("description", "")}
        )
        if retro_prompt:
            results["prompt"] = retro_prompt

        # Collect results from all previous phases
        if hasattr(self.memory_manager, "retrieve_with_edrr_phase"):
            expand_results = self.memory_manager.retrieve_with_edrr_phase(
                "EXPAND_RESULTS", "EXPAND", {"cycle_id": self.cycle_id}
            )
            differentiate_results = self.memory_manager.retrieve_with_edrr_phase(
                "DIFFERENTIATE_RESULTS", "DIFFERENTIATE", {"cycle_id": self.cycle_id}
            )
            refine_results = self.memory_manager.retrieve_with_edrr_phase(
                "REFINE_RESULTS", "REFINE", {"cycle_id": self.cycle_id}
            )
        else:
            expand_results = {}
            differentiate_results = {}
            refine_results = {}

        # Learning extraction methods
        learnings = self.wsde_team.extract_learnings(
            {
                "expand": expand_results,
                "differentiate": differentiate_results,
                "refine": refine_results,
                "task": self.task,
            },
            categorize_learnings=True,
        )
        results["learnings"] = learnings

        # Pattern recognition
        historical_context = []
        if hasattr(self.memory_manager, "retrieve_historical_patterns"):
            historical_context = self.memory_manager.retrieve_historical_patterns()
        patterns = self.wsde_team.recognize_patterns(
            learnings,
            historical_context=historical_context,
            code_analyzer=self.code_analyzer,
        )
        results["patterns"] = patterns

        # Knowledge integration
        integrated_knowledge = self.wsde_team.integrate_knowledge(
            learnings, patterns, memory_manager=self.memory_manager
        )
        results["integrated_knowledge"] = integrated_knowledge

        # Improvement suggestion generation
        improvement_suggestions = self.wsde_team.generate_improvement_suggestions(
            learnings,
            patterns,
            refine_results.get("quality_checks", {}),
            categorize_by_phase=True,
        )
        results["improvement_suggestions"] = improvement_suggestions

        # Initialize micro_cycle_results if it doesn't exist
        if "micro_cycle_results" not in results:
            results["micro_cycle_results"] = {}

        # If this is a micro cycle, integrate results with parent cycle
        if self.recursion_depth > 0 and self.parent_cycle_id and self.parent_phase:
            # Prepare the micro cycle results for integration
            micro_cycle_results = {
                "task": self.task,
                "learnings": learnings,
                "patterns": patterns,
                "improvement_suggestions": improvement_suggestions,
                "status": "completed",
            }

            # Store the micro cycle results for potential retrieval by the parent cycle
            self.memory_manager.store_with_edrr_phase(
                micro_cycle_results,
                "MICRO_CYCLE_RESULTS",
                self.parent_phase.value,
                {
                    "parent_cycle_id": self.parent_cycle_id,
                    "micro_cycle_id": self.cycle_id,
                },
            )

        # Final report generation
        final_report = self.generate_final_report(
            {
                "task": self.task,
                "expand": expand_results,
                "differentiate": differentiate_results,
                "refine": refine_results,
                "retrospect": results,
            }
        )
        results["final_report"] = final_report

        # Store results in memory with phase tag
        self.memory_manager.store_with_edrr_phase(
            results,
            "RETROSPECT_RESULTS",
            "RETROSPECT",
            {"cycle_id": self.cycle_id, "recursion_depth": self.recursion_depth},
        )

        # Create micro cycles for any provided sub tasks
        self._maybe_create_micro_cycles(context, Phase.RETROSPECT, results)

        # Store the final report
        self.memory_manager.store_with_edrr_phase(
            final_report,
            "FINAL_REPORT",
            "RETROSPECT",
            {"cycle_id": self.cycle_id, "recursion_depth": self.recursion_depth},
        )

        if self._enable_enhanced_logging:
            trace_data = {
                "timestamp": datetime.now().isoformat(),
                "inputs": context,
                "outputs": results,
                "metrics": {
                    "learnings_count": len(learnings),
                    "patterns_identified": len(patterns),
                    "improvement_suggestions": len(improvement_suggestions),
                },
            }

            # Add recursive information if this is a micro cycle
            if self.recursion_depth > 0:
                trace_data["parent_cycle_id"] = self.parent_cycle_id
                trace_data["recursion_depth"] = self.recursion_depth
                trace_data["parent_phase"] = (
                    self.parent_phase.value if self.parent_phase else None
                )

            self._execution_traces[f"RETROSPECT_{self.cycle_id}"] = trace_data

        logger.info(
            f"Retrospect phase completed with learnings extracted and final report generated (recursion depth: {self.recursion_depth})"
        )
        return results

    def generate_final_report(self, cycle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a final report for the EDRR cycle.

        Args:
            cycle_data: Data from all phases of the EDRR cycle

        Returns:
            The final report
        """
        logger.info(
            f"Generating final report for EDRR cycle (recursion depth: {self.recursion_depth})"
        )

        task = cycle_data.get("task", {})
        expand_results = cycle_data.get("expand", {})
        differentiate_results = cycle_data.get("differentiate", {})
        refine_results = cycle_data.get("refine", {})
        retrospect_results = cycle_data.get("retrospect", {})

        # Create a structured final report
        report = {
            "title": f"EDRR Cycle Report: {task.get('description', 'Unknown Task')}",
            "cycle_id": self.cycle_id,
            "timestamp": datetime.now().isoformat(),
            "task_summary": task,
            "process_summary": {
                "expand": {
                    "ideas_generated": len(expand_results.get("ideas", [])),
                    "knowledge_items": len(expand_results.get("knowledge", [])),
                    "key_insights": self._extract_key_insights(expand_results),
                },
                "differentiate": {
                    "options_evaluated": len(
                        differentiate_results.get("evaluated_options", [])
                    ),
                    "trade_offs": differentiate_results.get("trade_offs", []),
                    "decision_criteria": differentiate_results.get(
                        "decision_criteria", {}
                    ),
                },
                "refine": {
                    "selected_option": refine_results.get("selected_option", {}),
                    "implementation_summary": self._summarize_implementation(
                        refine_results.get("implementation_plan", [])
                    ),
                    "quality_assessment": self._summarize_quality_checks(
                        refine_results.get("quality_checks", {})
                    ),
                },
                "retrospect": {
                    "key_learnings": self._extract_key_learnings(
                        retrospect_results.get("learnings", [])
                    ),
                    "patterns": retrospect_results.get("patterns", []),
                    "improvement_suggestions": retrospect_results.get(
                        "improvement_suggestions", []
                    ),
                },
            },
            "outcome": {
                "solution": refine_results.get(
                    "optimized_plan", refine_results.get("implementation_plan", {})
                ),
                "next_steps": self._generate_next_steps(cycle_data),
                "future_considerations": self._extract_future_considerations(
                    retrospect_results
                ),
            },
        }

        # Add recursive information if this is a micro cycle
        if self.recursion_depth > 0:
            report["recursion_info"] = {
                "recursion_depth": self.recursion_depth,
                "parent_cycle_id": self.parent_cycle_id,
                "parent_phase": self.parent_phase.value if self.parent_phase else None,
            }

            # Add information about child cycles if any
            if self.child_cycles:
                report["child_cycles"] = [
                    {
                        "cycle_id": child.cycle_id,
                        "task": child.task,
                        "recursion_depth": child.recursion_depth,
                    }
                    for child in self.child_cycles
                ]

        # Add information about micro cycle results if any
        micro_cycle_results = {}
        for phase in [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]:
            if phase in self.results and "micro_cycle_results" in self.results[phase]:
                micro_cycle_results[phase.value] = self.results[phase][
                    "micro_cycle_results"
                ]

        if micro_cycle_results:
            report["micro_cycle_results"] = micro_cycle_results

        # Include aggregated performance metrics and basic recursion stats
        report["metrics"] = self.get_performance_metrics()
        report["child_cycle_count"] = len(self.child_cycles)

        logger.info(
            f"Final report generated for cycle {self.cycle_id} (recursion depth: {self.recursion_depth})"
        )
        return report

    def _extract_key_insights(self, expand_results: Dict[str, Any]) -> List[str]:
        """Extract key insights from expand phase results."""

        insights: List[str] = []

        ideas = expand_results.get("ideas", [])
        if ideas:
            idea_names = [str(i.get("idea", i)) for i in ideas[:3]]
            insights.append(f"Top ideas: {', '.join(idea_names)}")

        knowledge_items = expand_results.get("knowledge", [])
        if knowledge_items:
            insights.append(f"Retrieved {len(knowledge_items)} knowledge items")

        code_elements = expand_results.get("code_elements")
        if isinstance(code_elements, dict):
            counts = [f"{k}={v}" for k, v in code_elements.items()]
            insights.append("Code structure -> " + ", ".join(counts))
        elif code_elements:
            insights.append(f"Code elements count: {len(code_elements)}")

        return insights

    def _summarize_implementation(
        self, implementation_plan: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Summarize the implementation plan."""

        steps = len(implementation_plan)
        components: Set[str] = set()
        for step in implementation_plan:
            component = step.get("component")
            if component:
                components.add(str(component))

        if steps > 10:
            complexity = "High"
        elif steps > 5:
            complexity = "Medium"
        else:
            complexity = "Low"

        return {
            "steps": steps,
            "estimated_complexity": complexity,
            "primary_components": sorted(components),
        }

    def _summarize_quality_checks(
        self, quality_checks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Summarize quality checks."""

        issues = quality_checks.get("issues", [])
        critical = [i for i in issues if i.get("severity") == "critical"]
        areas = {i.get("area") for i in issues if isinstance(i, dict) and i.get("area")}

        return {
            "issues_found": len(issues),
            "critical_issues": len(critical),
            "areas_of_concern": sorted(a for a in areas if a),
        }

    def _extract_key_learnings(self, learnings: List[Dict[str, Any]]) -> List[str]:
        """Extract key learnings."""

        if not learnings:
            return []

        summaries = []
        for item in learnings[:3]:
            if isinstance(item, dict):
                summaries.append(str(item.get("learning", item)))
            else:
                summaries.append(str(item))

        return summaries

    def _generate_next_steps(self, cycle_data: Dict[str, Any]) -> List[str]:
        """Generate recommended next steps."""

        steps = []
        refine = cycle_data.get("refine", {})
        retrospect = cycle_data.get("retrospect", {})

        if refine.get("optimized_plan"):
            steps.append("Execute optimized plan")
        elif refine.get("implementation_plan"):
            steps.append("Implement selected option")

        if retrospect.get("improvement_suggestions"):
            steps.append("Address improvement suggestions")

        if not steps:
            steps.append("Review cycle results with team")

        return steps

    def _extract_future_considerations(
        self, retrospect_results: Dict[str, Any]
    ) -> List[str]:
        """Extract future considerations."""

        considerations = []
        patterns = retrospect_results.get("patterns", [])
        suggestions = retrospect_results.get("improvement_suggestions", [])

        if patterns:
            considerations.append(f"Monitor {len(patterns)} pattern(s)")

        if suggestions:
            considerations.append(f"Track {len(suggestions)} improvement suggestions")

        return considerations

    def execute_current_phase(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the current phase of the EDRR cycle.

        Args:
            context: Optional context for the phase execution

        Returns:
            The results of the phase execution

        Raises:
            EDRRCoordinatorError: If no phase is currently active
        """
        if not self.current_phase:
            raise EDRRCoordinatorError("No active phase to execute")

        context = context or {}

        # Execute the appropriate phase
        phase_executors = {
            Phase.EXPAND: self._execute_expand_phase,
            Phase.DIFFERENTIATE: self._execute_differentiate_phase,
            Phase.REFINE: self._execute_refine_phase,
            Phase.RETROSPECT: self._execute_retrospect_phase,
        }

        executor = phase_executors.get(self.current_phase)
        if not executor:
            raise EDRRCoordinatorError(
                f"No executor available for phase {self.current_phase}"
            )

        try:
            results = executor(context)
            self.results[self.current_phase.name] = results
            return results
        except Exception as e:
            logger.error(f"Error executing phase {self.current_phase.value}: {str(e)}")
            raise EDRRCoordinatorError(
                f"Failed to execute phase {self.current_phase.value}: {e}"
            )

    def generate_report(self) -> Dict[str, Any]:
        """Generate a high level report for the entire cycle."""
        phase_data = {phase.name: self.results.get(phase.name, {}) for phase in Phase}
        final_report = self.generate_final_report(
            {
                "task": self.task,
                "expand": self.results.get(Phase.EXPAND.name, {}),
                "differentiate": self.results.get(Phase.DIFFERENTIATE.name, {}),
                "refine": self.results.get(Phase.REFINE.name, {}),
                "retrospect": self.results.get(Phase.RETROSPECT.name, {}),
            }
        )
        return {
            "task": self.task,
            "cycle_id": self.cycle_id,
            "timestamp": datetime.now().isoformat(),
            "phases": phase_data,
            "summary": final_report,
        }

    def get_execution_traces(self) -> Dict[str, Any]:
        """Return collected execution traces."""
        return copy.deepcopy(self._execution_traces) if self._execution_traces else {}

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Return chronological execution history events."""
        return list(self._execution_history) if self._execution_history else []

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return simple performance metrics for each phase."""
        return copy.deepcopy(self.performance_metrics)

    def _aggregate_results(self) -> None:
        """Aggregate results from all phases and child cycles."""
        aggregated = {}
        for phase in [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]:
            if phase.name in self.results:
                aggregated[phase.value] = self.results[phase.name]

        if self.child_cycles:
            aggregated["child_cycles"] = {
                c.cycle_id: c.results for c in self.child_cycles
            }

        self.results["AGGREGATED"] = aggregated

        # Aggregate performance metrics across phases
        total_duration = sum(
            m.get("duration", 0) for m in self.performance_metrics.values()
        )
        self.performance_metrics["TOTAL"] = {"duration": total_duration}
