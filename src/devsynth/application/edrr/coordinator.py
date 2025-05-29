"""EDRR Coordinator module.

This module defines the EDRRCoordinator class that orchestrates the flow between
components according to the EDRR (Expand, Differentiate, Refine, Retrospect) pattern.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
from pathlib import Path

from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
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
    """

    def __init__(self, memory_manager: MemoryManager, wsde_team: WSDETeam,
                 code_analyzer: CodeAnalyzer, ast_transformer: AstTransformer,
                 prompt_manager: PromptManager, documentation_manager: DocumentationManager,
                 enable_enhanced_logging: bool = False):
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
        """
        self.memory_manager = memory_manager
        self.wsde_team = wsde_team
        self.code_analyzer = code_analyzer
        self.ast_transformer = ast_transformer
        self.prompt_manager = prompt_manager
        self.documentation_manager = documentation_manager
        self._enable_enhanced_logging = enable_enhanced_logging
        self._execution_traces = {} if enable_enhanced_logging else None

        self.manifest_parser = ManifestParser()
        self._manifest_parser = None
        self.current_phase = None
        self.task = None
        self.results = {}
        self.cycle_id = None
        self.manifest = None

        logger.info("EDRR coordinator initialized")

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

        # Store the task in memory
        self.memory_manager.store_with_edrr_phase(
            self.task, "TASK", "EXPAND",
            {"cycle_id": self.cycle_id}
        )

        # Enter the Expand phase
        self.progress_to_phase(Phase.EXPAND)

        logger.info(f"Started EDRR cycle for task: {task.get('description', 'Unknown')}")

    def start_cycle_from_manifest(self, manifest_path_or_string: Union[str, Path], is_file: bool = True) -> None:
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
                self.manifest = self.manifest_parser.parse_string(manifest_path_or_string)

            # Start execution tracking
            self.manifest_parser.start_execution()

            # Create a task from the manifest
            self.task = {
                "id": self.manifest_parser.get_manifest_id(),
                "description": self.manifest_parser.get_manifest_description(),
                "metadata": self.manifest_parser.get_manifest_metadata()
            }

            self.cycle_id = str(uuid.uuid4())
            self.results = {}

            # Store the task and manifest in memory with enhanced traceability
            self.memory_manager.store_with_edrr_phase(
                self.task, "TASK", Phase.EXPAND.value,
                metadata={
                    "cycle_id": self.cycle_id, 
                    "from_manifest": True,
                    "manifest_id": self.manifest_parser.get_manifest_id(),
                    "execution_start_time": self.manifest_parser.execution_trace["start_time"]
                }
            )

            self.memory_manager.store_with_edrr_phase(
                self.manifest, "MANIFEST", Phase.EXPAND.value,
                metadata={
                    "cycle_id": self.cycle_id,
                    "execution_trace_id": self.manifest_parser.execution_trace.get("manifest_id")
                }
            )

            # Enter the Expand phase
            self.progress_to_phase(Phase.EXPAND)

            logger.info(f"Started EDRR cycle from manifest with ID: {self.task['id']} with enhanced traceability")
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
            if self.manifest and self.manifest_parser:
                # Check if dependencies are met
                if not self.manifest_parser.check_phase_dependencies(phase):
                    error_msg = f"Cannot progress to {phase.value} phase: dependencies not met"
                    logger.error(error_msg)
                    raise EDRRCoordinatorError(error_msg)

                # Start tracking the phase
                self.manifest_parser.start_phase(phase)

            # Store the phase transition in memory
            self.memory_manager.store_with_edrr_phase(
                {"from": "EXPAND", "to": "DIFFERENTIATE"},
                "PHASE_TRANSITION", 
                "DIFFERENTIATE",
                {"cycle_id": self.cycle_id}
            )

            # Update the current phase
            self.current_phase = phase

            # Execute the phase
            if phase == Phase.EXPAND:
                self._execute_expand_phase()
            elif phase == Phase.DIFFERENTIATE:
                self._execute_differentiate_phase()
            elif phase == Phase.REFINE:
                self._execute_refine_phase()
            elif phase == Phase.RETROSPECT:
                self._execute_retrospect_phase()

            # Complete tracking the phase if using a manifest
            if self.manifest and self.manifest_parser:
                self.manifest_parser.complete_phase(phase, self.results.get(phase))

            logger.info(f"Progressed to and completed {phase.value} phase for task: {self.task.get('description', 'Unknown')}")
        except ManifestParseError as e:
            logger.error(f"Failed to progress to phase {phase.value}: {e}")
            raise EDRRCoordinatorError(f"Failed to progress to phase {phase.value}: {e}")

    def _execute_expand_phase(self) -> None:
        """Execute the Expand phase of the EDRR cycle."""
        phase = Phase.EXPAND
        logger.info(f"Executing {phase.value} phase")

        # Get instructions and templates from manifest if available
        instructions = None
        manifest_templates = []
        manifest_resources = []

        if self.manifest:
            try:
                instructions = self.manifest_parser.get_phase_instructions(phase)
                manifest_templates = self.manifest_parser.get_phase_templates(phase)
                manifest_resources = self.manifest_parser.get_phase_resources(phase)
                logger.info(f"Using manifest instructions for {phase.value} phase")
            except ManifestParseError as e:
                logger.warning(f"Failed to get manifest data for {phase.value} phase: {e}")

        # Get prompt templates for the Expand phase
        templates = self.prompt_manager.list_templates(edrr_phase=phase.value)

        # Add manifest templates if available
        if manifest_templates:
            templates.extend(manifest_templates)
            logger.info(f"Added {len(manifest_templates)} templates from manifest for {phase.value} phase")

        # Retrieve relevant documentation
        docs = []

        # Add manifest resources if available
        if manifest_resources:
            for resource in manifest_resources:
                try:
                    resource_docs = self.documentation_manager.get_documentation(resource)
                    if resource_docs:
                        docs.append(resource_docs)
                        logger.info(f"Added resource '{resource}' from manifest")
                except Exception as e:
                    logger.warning(f"Failed to get resource '{resource}' from manifest: {e}")

        # Query for additional documentation
        query_docs = self.documentation_manager.query_documentation(
            self.task.get("description", ""),
            limit=5
        )
        docs.extend(query_docs)
        logger.info(f"Retrieved {len(docs)} documentation items for {phase.value} phase")

        # Analyze file structure if the task involves a file
        file_path = self.task.get("file_path")
        analysis = None
        if file_path:
            try:
                analysis = self.code_analyzer.analyze_file(file_path)
                logger.info(f"Analyzed file structure for {file_path}")
            except Exception as e:
                logger.error(f"Failed to analyze file structure: {e}")

        # Prepare input for WSDE team
        wsde_input = {
            "id": self.task.get("id"),
            "description": self.task.get("description"),
            "documentation": docs,
            "analysis": analysis,
            "templates": templates
        }

        # Add instructions if available
        if instructions:
            wsde_input["instructions"] = instructions

        # Log the input to the WSDE team
        logger.info(f"Instructing WSDE team for {phase.value} phase with {len(templates)} templates and {len(docs)} documentation items")

        # Instruct the WSDE team to brainstorm approaches
        approaches = self.wsde_team.brainstorm_approaches(self.task)
        logger.info(f"WSDE team generated {len(approaches)} approaches")

        # Store the results in memory
        self.results[phase] = {
            "wsde_brainstorm": approaches,
            "documentation": docs,
            "analysis": analysis,
            "instructions": instructions,
            "templates": templates,
            "resources": manifest_resources,
            "completed": True,
            "timestamp": datetime.now().isoformat()
        }

        # Log the results
        logger.info(f"Completed {phase.value} phase with {len(approaches)} approaches")

        # Store the results in memory
        self.memory_manager.store_with_edrr_phase(
            self.results[phase],
            "RESULT",
            phase.value,
            metadata={
                "cycle_id": self.cycle_id, 
                "task_id": self.task.get("id"),
                "from_manifest": self.manifest is not None,
                "timestamp": datetime.now().isoformat()
            }
        )

    def _execute_differentiate_phase(self) -> None:
        """Execute the Differentiate phase of the EDRR cycle."""
        phase = Phase.DIFFERENTIATE
        logger.info(f"Executing {phase.value} phase")

        # Get instructions and templates from manifest if available
        instructions = None
        manifest_templates = []
        manifest_resources = []

        if self.manifest:
            try:
                instructions = self.manifest_parser.get_phase_instructions(phase)
                manifest_templates = self.manifest_parser.get_phase_templates(phase)
                manifest_resources = self.manifest_parser.get_phase_resources(phase)
                logger.info(f"Using manifest instructions for {phase.value} phase")
            except ManifestParseError as e:
                logger.warning(f"Failed to get manifest data for {phase.value} phase: {e}")

        # Get prompt templates for the Differentiate phase
        templates = self.prompt_manager.list_templates(edrr_phase=phase.value)

        # Add manifest templates if available
        if manifest_templates:
            templates.extend(manifest_templates)
            logger.info(f"Added {len(manifest_templates)} templates from manifest for {phase.value} phase")

        # Retrieve relevant documentation
        docs = []

        # Add manifest resources if available
        if manifest_resources:
            for resource in manifest_resources:
                try:
                    resource_docs = self.documentation_manager.get_documentation(resource)
                    if resource_docs:
                        docs.append(resource_docs)
                        logger.info(f"Added resource '{resource}' from manifest")
                except Exception as e:
                    logger.warning(f"Failed to get resource '{resource}' from manifest: {e}")

        # Query for additional documentation
        query_docs = self.documentation_manager.query_documentation(
            f"best practices {self.task.get('description', '')}",
            limit=5
        )
        docs.extend(query_docs)
        logger.info(f"Retrieved {len(docs)} documentation items for {phase.value} phase")

        # Get the approaches from the Expand phase
        expand_results = self.results.get(Phase.EXPAND, {})
        approaches = expand_results.get("approaches", [])
        logger.info(f"Retrieved {len(approaches)} approaches from Expand phase")

        # Evaluate code quality if there's code to evaluate
        code_to_evaluate = self.task.get("code")
        quality_analysis = None
        if code_to_evaluate:
            try:
                quality_analysis = self.code_analyzer.analyze_code(code_to_evaluate)
                logger.info("Analyzed code quality")
            except Exception as e:
                logger.error(f"Failed to analyze code quality: {e}")

        # Prepare input for WSDE team
        wsde_input = {
            "id": self.task.get("id"),
            "description": self.task.get("description"),
            "approaches": approaches,
            "documentation": docs,
            "quality_analysis": quality_analysis,
            "templates": templates
        }

        # Add instructions if available
        if instructions:
            wsde_input["instructions"] = instructions

        # Log the input to the WSDE team
        logger.info(f"Instructing WSDE team for {phase.value} phase with {len(templates)} templates and {len(docs)} documentation items")

        # Instruct the WSDE team to evaluate and compare approaches
        evaluation = self.wsde_team.evaluate_approaches(approaches)
        logger.info("WSDE team completed evaluation of approaches")

        # Store the results in memory
        self.results[phase] = {
            "evaluation": evaluation,
            "documentation": docs,
            "quality_analysis": quality_analysis,
            "instructions": instructions,
            "templates": templates,
            "resources": manifest_resources,
            "completed": True,
            "timestamp": datetime.now().isoformat()
        }

        # Log the results
        selected_approach = evaluation.get("selected_approach", {})
        logger.info(f"Completed {phase.value} phase, selected approach: {selected_approach.get('name', 'Unknown')}")

        # Store the results in memory
        self.memory_manager.store_with_edrr_phase(
            self.results[phase],
            "RESULT",
            phase.value,
            metadata={
                "cycle_id": self.cycle_id, 
                "task_id": self.task.get("id"),
                "from_manifest": self.manifest is not None,
                "timestamp": datetime.now().isoformat()
            }
        )

    def _execute_refine_phase(self) -> None:
        """Execute the Refine phase of the EDRR cycle."""
        phase = Phase.REFINE
        logger.info(f"Executing {phase.value} phase")

        # Get instructions and templates from manifest if available
        instructions = None
        manifest_templates = []
        manifest_resources = []

        if self.manifest:
            try:
                instructions = self.manifest_parser.get_phase_instructions(phase)
                manifest_templates = self.manifest_parser.get_phase_templates(phase)
                manifest_resources = self.manifest_parser.get_phase_resources(phase)
                logger.info(f"Using manifest instructions for {phase.value} phase")
            except ManifestParseError as e:
                logger.warning(f"Failed to get manifest data for {phase.value} phase: {e}")

        # Get prompt templates for the Refine phase
        templates = self.prompt_manager.list_templates(edrr_phase=phase.value)

        # Add manifest templates if available
        if manifest_templates:
            templates.extend(manifest_templates)
            logger.info(f"Added {len(manifest_templates)} templates from manifest for {phase.value} phase")

        # Retrieve relevant documentation
        docs = []

        # Add manifest resources if available
        if manifest_resources:
            for resource in manifest_resources:
                try:
                    resource_docs = self.documentation_manager.get_documentation(resource)
                    if resource_docs:
                        docs.append(resource_docs)
                        logger.info(f"Added resource '{resource}' from manifest")
                except Exception as e:
                    logger.warning(f"Failed to get resource '{resource}' from manifest: {e}")

        # Query for additional documentation
        query_docs = self.documentation_manager.query_documentation(
            f"implementation examples {self.task.get('description', '')}",
            limit=5
        )
        docs.extend(query_docs)
        logger.info(f"Retrieved {len(docs)} documentation items for {phase.value} phase")

        # Get the evaluation from the Differentiate phase
        differentiate_results = self.results.get(Phase.DIFFERENTIATE, {})
        evaluation = differentiate_results.get("evaluation", {})
        logger.info("Retrieved evaluation from Differentiate phase")

        # Apply code transformations if needed
        code_to_transform = evaluation.get("selected_approach", {}).get("code")
        transformed_code = None
        if code_to_transform:
            try:
                # This is a simplified example - in a real implementation, we would
                # determine what transformations to apply based on the evaluation
                transformed_code = self.ast_transformer.rename_identifier(
                    code_to_transform,
                    "old_name",
                    "new_name"
                )
                logger.info("Applied code transformations")
            except Exception as e:
                logger.error(f"Failed to apply code transformations: {e}")

        # Prepare input for WSDE team
        wsde_input = {
            "id": self.task.get("id"),
            "description": self.task.get("description"),
            "selected_approach": evaluation.get("selected_approach"),
            "documentation": docs,
            "transformed_code": transformed_code,
            "templates": templates
        }

        # Add instructions if available
        if instructions:
            wsde_input["instructions"] = instructions

        # Log the input to the WSDE team
        logger.info(f"Instructing WSDE team for {phase.value} phase with {len(templates)} templates and {len(docs)} documentation items")

        # Instruct the WSDE team to implement the selected approach
        implementation = self.wsde_team.implement_approach(evaluation.get("selected_approach"))
        logger.info("WSDE team completed implementation")

        # Store the results in memory
        self.results[phase] = {
            "implementation": implementation,
            "documentation": docs,
            "transformed_code": transformed_code,
            "instructions": instructions,
            "templates": templates,
            "resources": manifest_resources,
            "completed": True,
            "timestamp": datetime.now().isoformat()
        }

        # Log the results
        logger.info(f"Completed {phase.value} phase")

        # Store the results in memory
        self.memory_manager.store_with_edrr_phase(
            self.results[phase],
            "RESULT",
            phase.value,
            metadata={
                "cycle_id": self.cycle_id, 
                "task_id": self.task.get("id"),
                "from_manifest": self.manifest is not None,
                "timestamp": datetime.now().isoformat()
            }
        )

    def _execute_retrospect_phase(self) -> None:
        """Execute the Retrospect phase of the EDRR cycle."""
        phase = Phase.RETROSPECT
        logger.info(f"Executing {phase.value} phase")

        # Get instructions and templates from manifest if available
        instructions = None
        manifest_templates = []
        manifest_resources = []

        if self.manifest:
            try:
                instructions = self.manifest_parser.get_phase_instructions(phase)
                manifest_templates = self.manifest_parser.get_phase_templates(phase)
                manifest_resources = self.manifest_parser.get_phase_resources(phase)
                logger.info(f"Using manifest instructions for {phase.value} phase")
            except ManifestParseError as e:
                logger.warning(f"Failed to get manifest data for {phase.value} phase: {e}")

        # Get prompt templates for the Retrospect phase
        templates = self.prompt_manager.list_templates(edrr_phase=phase.value)

        # Add manifest templates if available
        if manifest_templates:
            templates.extend(manifest_templates)
            logger.info(f"Added {len(manifest_templates)} templates from manifest for {phase.value} phase")

        # Retrieve relevant documentation
        docs = []

        # Add manifest resources if available
        if manifest_resources:
            for resource in manifest_resources:
                try:
                    resource_docs = self.documentation_manager.get_documentation(resource)
                    if resource_docs:
                        docs.append(resource_docs)
                        logger.info(f"Added resource '{resource}' from manifest")
                except Exception as e:
                    logger.warning(f"Failed to get resource '{resource}' from manifest: {e}")

        # Query for additional documentation
        query_docs = self.documentation_manager.query_documentation(
            f"evaluation criteria {self.task.get('description', '')}",
            limit=5
        )
        docs.extend(query_docs)
        logger.info(f"Retrieved {len(docs)} documentation items for {phase.value} phase")

        # Get the implementation from the Refine phase
        refine_results = self.results.get(Phase.REFINE, {})
        implementation = refine_results.get("implementation", {})
        logger.info("Retrieved implementation from Refine phase")

        # Verify code quality if there's code to verify
        code_to_verify = implementation.get("code")
        is_valid = None
        if code_to_verify:
            try:
                is_valid = self.ast_transformer.validate_syntax(code_to_verify)
                logger.info(f"Validated code syntax: {'valid' if is_valid else 'invalid'}")
            except Exception as e:
                logger.error(f"Failed to validate code syntax: {e}")

        # Prepare input for WSDE team
        wsde_input = {
            "id": self.task.get("id"),
            "description": self.task.get("description"),
            "implementation": implementation,
            "documentation": docs,
            "is_valid": is_valid,
            "templates": templates
        }

        # Add instructions if available
        if instructions:
            wsde_input["instructions"] = instructions

        # Log the input to the WSDE team
        logger.info(f"Instructing WSDE team for {phase.value} phase with {len(templates)} templates and {len(docs)} documentation items")

        # Instruct the WSDE team to evaluate the implementation
        evaluation = self.wsde_team.evaluate_implementation(implementation)
        logger.info("WSDE team completed evaluation of implementation")

        # Store the results in memory
        self.results[phase] = {
            "evaluation": evaluation,
            "documentation": docs,
            "is_valid": is_valid,
            "instructions": instructions,
            "templates": templates,
            "resources": manifest_resources,
            "completed": True,
            "timestamp": datetime.now().isoformat()
        }

        # Log the results
        success = evaluation.get("success", False)
        logger.info(f"Completed {phase.value} phase, implementation success: {success}")

        # Store the results in memory
        self.memory_manager.store_with_edrr_phase(
            self.results[phase],
            "RESULT",
            phase.value,
            metadata={
                "cycle_id": self.cycle_id, 
                "task_id": self.task.get("id"),
                "from_manifest": self.manifest is not None,
                "timestamp": datetime.now().isoformat()
            }
        )

        # Generate a final report
        logger.info("Generating final report")
        self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a final report summarizing the entire EDRR cycle.

        Returns:
            A dictionary containing the report
        """
        # Collect metrics and statistics
        expand_results = self.results.get(Phase.EXPAND, {})
        differentiate_results = self.results.get(Phase.DIFFERENTIATE, {})
        refine_results = self.results.get(Phase.REFINE, {})
        retrospect_results = self.results.get(Phase.RETROSPECT, {})

        approaches_count = len(expand_results.get("approaches", []))
        selected_approach = differentiate_results.get("evaluation", {}).get("selected_approach", {})
        implementation_success = retrospect_results.get("is_valid", False)
        final_evaluation = retrospect_results.get("evaluation", {})

        # Log detailed metrics
        logger.info(f"EDRR Cycle Metrics - Approaches: {approaches_count}, Implementation Success: {implementation_success}")

        # Complete execution tracking if using a manifest
        execution_trace = None
        if self.manifest and self.manifest_parser:
            try:
                execution_trace = self.manifest_parser.complete_execution()
                logger.info(f"Completed execution tracking for manifest: {self.manifest_parser.get_manifest_id()}")
            except ManifestParseError as e:
                logger.warning(f"Failed to complete execution tracking: {e}")

        # Create the report with enhanced traceability
        report = {
            "task": self.task,
            "cycle_id": self.cycle_id,
            "timestamp": datetime.now().isoformat(),
            "phases": {
                "EXPAND": expand_results,
                "DIFFERENTIATE": differentiate_results,
                "REFINE": refine_results,
                "RETROSPECT": retrospect_results
            },
            "summary": {
                "approaches_count": approaches_count,
                "selected_approach": selected_approach,
                "implementation_success": implementation_success,
                "final_evaluation": final_evaluation
            },
            "traceability": {
                "start_time": expand_results.get("timestamp"),
                "end_time": retrospect_results.get("timestamp"),
                "phase_durations": {
                    Phase.EXPAND.value: self._calculate_phase_duration(Phase.EXPAND),
                    Phase.DIFFERENTIATE.value: self._calculate_phase_duration(Phase.DIFFERENTIATE),
                    Phase.REFINE.value: self._calculate_phase_duration(Phase.REFINE),
                    Phase.RETROSPECT.value: self._calculate_phase_duration(Phase.RETROSPECT)
                }
            }
        }

        # Add manifest information and execution trace if available
        if self.manifest and self.manifest_parser:
            report["manifest"] = {
                "id": self.manifest_parser.get_manifest_id(),
                "description": self.manifest_parser.get_manifest_description(),
                "metadata": self.manifest_parser.get_manifest_metadata()
            }

            if execution_trace:
                report["execution_trace"] = execution_trace

                # Add detailed phase metrics from execution trace
                report["traceability"]["detailed_metrics"] = {
                    "total_duration": execution_trace.get("duration"),
                    "all_phases_completed": execution_trace.get("completed"),
                    "phase_status": {
                        phase.value: self.manifest_parser.get_phase_status(phase)
                        for phase in Phase
                    }
                }

                logger.info(f"Added execution trace to report with {len(execution_trace.get('phases', {}))} phases")

            logger.info(f"Added manifest information to report: {report['manifest']['id']}")

        # Store the report in memory with enhanced metadata
        metadata = {
            "cycle_id": self.cycle_id, 
            "task_id": self.task.get("id"),
            "from_manifest": self.manifest is not None,
            "timestamp": datetime.now().isoformat(),
            "report_type": "comprehensive" if execution_trace else "standard"
        }

        # Add execution trace metadata if available
        if execution_trace:
            metadata.update({
                "execution_trace_id": execution_trace.get("manifest_id"),
                "execution_duration": execution_trace.get("duration"),
                "execution_completed": execution_trace.get("completed")
            })

        self.memory_manager.store_with_edrr_phase(
            report,
            "REPORT",
            "report",
            metadata=metadata
        )

        logger.info(f"Generated final report for task: {self.task.get('description', 'Unknown')} with enhanced traceability")
        return report

    def _calculate_phase_duration(self, phase: Phase) -> Optional[float]:
        """
        Calculate the duration of a phase in seconds.

        Args:
            phase: The phase to calculate the duration for

        Returns:
            The duration in seconds, or None if the phase timestamps are not available
        """
        try:
            # Get the phase results
            phase_results = self.results.get(phase, {})

            # Check if the phase has a timestamp
            if "timestamp" not in phase_results:
                return None

            # Get the timestamp of the current phase
            phase_time = datetime.fromisoformat(phase_results["timestamp"])

            # Get the timestamp of the previous phase
            prev_phase = None
            if phase == Phase.DIFFERENTIATE:
                prev_phase = Phase.EXPAND
            elif phase == Phase.REFINE:
                prev_phase = Phase.DIFFERENTIATE
            elif phase == Phase.RETROSPECT:
                prev_phase = Phase.REFINE

            if prev_phase:
                prev_phase_results = self.results.get(prev_phase, {})
                if "timestamp" in prev_phase_results:
                    prev_phase_time = datetime.fromisoformat(prev_phase_results["timestamp"])
                    # Calculate the duration in seconds
                    return (phase_time - prev_phase_time).total_seconds()

            return None
        except Exception as e:
            logger.warning(f"Failed to calculate phase duration: {e}")
            return None

    def get_execution_traces(self) -> Dict[str, Any]:
        """
        Get the execution traces for the current EDRR cycle.

        Returns:
            A dictionary containing the execution traces
        """
        if not self._enable_enhanced_logging:
            logger.warning("Enhanced logging is not enabled, execution traces are not available")
            return {}

        # Create a comprehensive trace structure
        traces = {
            "cycle_id": self.cycle_id,
            "phases": {},
            "overall_status": "completed" if Phase.RETROSPECT in self.results else "in_progress",
            "metadata": {
                "task_id": self.task.get("id") if self.task else None,
                "from_manifest": self.manifest is not None,
                "start_time": self.results.get(Phase.EXPAND, {}).get("timestamp"),
                "end_time": self.results.get(Phase.RETROSPECT, {}).get("timestamp")
            }
        }

        # Add phase-specific traces
        for phase in Phase:
            if phase in self.results:
                phase_results = self.results[phase]
                traces["phases"][phase.name] = {
                    "status": "completed" if phase_results.get("completed", False) else "in_progress",
                    "start_time": phase_results.get("timestamp"),
                    "end_time": phase_results.get("timestamp"),  # This is a simplification
                    "metrics": {
                        "duration": self._calculate_phase_duration(phase),
                        "memory_usage": len(str(phase_results)),  # Simplified metric
                        "component_calls": {
                            "wsde_team": 1,  # Simplified metric
                            "code_analyzer": 1 if phase_results.get("analysis") else 0,
                            "documentation_manager": len(phase_results.get("documentation", []))
                        }
                    }
                }

        return traces

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get the execution history for the current EDRR cycle.

        Returns:
            A list of dictionaries containing the execution history entries
        """
        if not self._enable_enhanced_logging:
            logger.warning("Enhanced logging is not enabled, execution history is not available")
            return []

        history = []

        # Add entries for each phase
        for phase in Phase:
            if phase in self.results:
                phase_results = self.results[phase]

                # Add phase start entry
                history.append({
                    "timestamp": phase_results.get("timestamp"),
                    "phase": phase.name,
                    "action": "START",
                    "details": {
                        "task_id": self.task.get("id") if self.task else None,
                        "cycle_id": self.cycle_id
                    }
                })

                # Add phase completion entry
                if phase_results.get("completed", False):
                    history.append({
                        "timestamp": phase_results.get("timestamp"),  # This is a simplification
                        "phase": phase.name,
                        "action": "COMPLETE",
                        "details": {
                            "task_id": self.task.get("id") if self.task else None,
                            "cycle_id": self.cycle_id,
                            "result_summary": {
                                "approaches_count": len(phase_results.get("approaches", [])) if phase == Phase.EXPAND else None,
                                "selected_approach": phase_results.get("evaluation", {}).get("selected_approach", {}).get("id") if phase == Phase.DIFFERENTIATE else None,
                                "implementation_success": phase_results.get("is_valid", False) if phase == Phase.RETROSPECT else None
                            }
                        }
                    })

        return history

    def get_performance_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for the current EDRR cycle.

        Returns:
            A dictionary containing performance metrics for each phase
        """
        if not self._enable_enhanced_logging:
            logger.warning("Enhanced logging is not enabled, performance metrics are not available")
            return {}

        metrics = {}

        # Add metrics for each phase
        for phase in Phase:
            if phase in self.results:
                phase_results = self.results[phase]

                metrics[phase.name] = {
                    "duration": self._calculate_phase_duration(phase),
                    "memory_usage": len(str(phase_results)),  # Simplified metric
                    "component_calls": {
                        "wsde_team": 1,  # Simplified metric
                        "code_analyzer": 1 if phase_results.get("analysis") else 0,
                        "documentation_manager": len(phase_results.get("documentation", []))
                    }
                }

        return metrics
