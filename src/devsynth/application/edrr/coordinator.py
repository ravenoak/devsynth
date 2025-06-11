"""EDRR Coordinator module.

This module defines the EDRRCoordinator class that orchestrates the flow between
components according to the EDRR (Expand, Differentiate, Refine, Retrospect) pattern.

The coordinator supports recursive EDRR cycles, where each macro phase can contain
its own nested micro-EDRR cycles, creating a fractal structure that enables
self-optimization at multiple levels of granularity.
"""

from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime
import uuid
from pathlib import Path
import copy

from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.manifest_parser import ManifestParser, ManifestParseError
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

# Create a logger for this module
logger = DevSynthLogger(__name__)


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
        self._enable_enhanced_logging = enable_enhanced_logging
        self._execution_traces = {} if enable_enhanced_logging else None
        self._execution_history = [] if enable_enhanced_logging else None
        self.performance_metrics: Dict[str, Any] = {}

        # Recursive EDRR attributes
        self.parent_cycle_id = parent_cycle_id
        self.recursion_depth = recursion_depth
        self.parent_phase = parent_phase
        self.child_cycles = []
        self.max_recursion_depth = self.DEFAULT_MAX_RECURSION_DEPTH

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
        """
        Start a new EDRR cycle with the given task.

        Args:
            task: The task to process
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

        # Initial role assignment before the first phase
        self.wsde_team.assign_roles()
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
        """
        try:
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

            # Initial role assignment before the first phase
            self.wsde_team.assign_roles()
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

            # Assign roles for the new phase
            self.wsde_team.assign_roles()
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

            # Complete tracking the phase if using a manifest
            if self.manifest is not None and self.manifest_parser:
                self.manifest_parser.complete_phase(phase, self.results.get(phase))

            logger.info(
                f"Progressed to and completed {phase.value} phase for task: {self.task.get('description', 'Unknown')}"
            )
        except ManifestParseError as e:
            logger.error(f"Failed to progress to phase {phase.value}: {e}")
            raise EDRRCoordinatorError(
                f"Failed to progress to phase {phase.value}: {e}"
            )

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

        # Start the micro cycle with the given task
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
            "task": task,
            "status": "created",
        }

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
        detailed_plan = self.wsde_team.elaborate_details(
            selected_option,
            detail_level="high",
            include_edge_cases=True,
            consider_constraints=True,
        )
        results["detailed_plan"] = detailed_plan

        # Implementation planning
        implementation_plan = self.wsde_team.create_implementation_plan(
            detailed_plan,
            code_analyzer=self.code_analyzer,
            ast_transformer=self.ast_transformer,
            include_testing_strategy=True,
        )
        results["implementation_plan"] = implementation_plan

        # Optimization algorithms
        optimized_plan = self.wsde_team.optimize_implementation(
            implementation_plan,
            optimization_targets=["performance", "readability", "maintainability"],
            code_analyzer=self.code_analyzer,
        )
        results["optimized_plan"] = optimized_plan

        # Quality assurance checks
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
        results["quality_checks"] = quality_checks

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

        logger.info(
            f"Final report generated for cycle {self.cycle_id} (recursion depth: {self.recursion_depth})"
        )
        return report

    def _extract_key_insights(self, expand_results: Dict[str, Any]) -> List[str]:
        """Extract key insights from expand phase results"""
        # Implementation would extract most significant findings
        return ["Key insight 1", "Key insight 2", "Key insight 3"]

    def _summarize_implementation(
        self, implementation_plan: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Summarize the implementation plan"""
        # Implementation would create a concise summary
        return {
            "steps": len(implementation_plan),
            "estimated_complexity": "Medium",
            "primary_components": ["Component A", "Component B"],
        }

    def _summarize_quality_checks(
        self, quality_checks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Summarize quality checks"""
        # Implementation would create a summary of quality assessment
        return {
            "issues_found": len(quality_checks),
            "critical_issues": 0,
            "areas_of_concern": ["Area 1", "Area 2"],
        }

    def _extract_key_learnings(self, learnings: List[Dict[str, Any]]) -> List[str]:
        """Extract key learnings"""
        # Implementation would extract most important learnings
        return ["Key learning 1", "Key learning 2", "Key learning 3"]

    def _generate_next_steps(self, cycle_data: Dict[str, Any]) -> List[str]:
        """Generate recommended next steps"""
        # Implementation would create actionable next steps
        return [
            "Implement core functionality",
            "Create test suite",
            "Update documentation",
        ]

    def _extract_future_considerations(
        self, retrospect_results: Dict[str, Any]
    ) -> List[str]:
        """Extract future considerations"""
        # Implementation would identify important future considerations
        return [
            "Consider scaling strategy",
            "Evaluate performance under high load",
            "Plan for internationalization",
        ]

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
