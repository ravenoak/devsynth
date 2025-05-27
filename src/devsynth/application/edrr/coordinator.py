"""EDRR Coordinator module.

This module defines the EDRRCoordinator class that orchestrates the flow between
components according to the EDRR (Expand, Differentiate, Refine, Retrospect) pattern.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class EDRRCoordinator:
    """
    Coordinates the flow between components according to the EDRR pattern.
    
    This class orchestrates the interaction between the memory system, WSDE team,
    AST analyzer, prompt manager, and documentation manager to implement the
    EDRR (Expand, Differentiate, Refine, Retrospect) workflow.
    """
    
    def __init__(self, memory_manager: MemoryManager, wsde_team: WSDETeam,
                 code_analyzer: CodeAnalyzer, ast_transformer: AstTransformer,
                 prompt_manager: PromptManager, documentation_manager: DocumentationManager):
        """
        Initialize the EDRR coordinator.
        
        Args:
            memory_manager: The memory manager to use
            wsde_team: The WSDE team to coordinate
            code_analyzer: The code analyzer to use
            ast_transformer: The AST transformer to use
            prompt_manager: The prompt manager to use
            documentation_manager: The documentation manager to use
        """
        self.memory_manager = memory_manager
        self.wsde_team = wsde_team
        self.code_analyzer = code_analyzer
        self.ast_transformer = ast_transformer
        self.prompt_manager = prompt_manager
        self.documentation_manager = documentation_manager
        
        self.current_phase = None
        self.task = None
        self.results = {}
        self.cycle_id = None
        
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
        
        # Store the task in memory
        self.memory_manager.store_with_edrr_phase(
            self.task, "TASK", Phase.EXPAND.value,
            metadata={"cycle_id": self.cycle_id}
        )
        
        # Enter the Expand phase
        self.progress_to_phase(Phase.EXPAND)
        
        logger.info(f"Started EDRR cycle for task: {task.get('description', 'Unknown')}")
    
    def progress_to_phase(self, phase: Phase) -> None:
        """
        Progress to the specified phase.
        
        Args:
            phase: The phase to progress to
        """
        # Store the phase transition in memory
        self.memory_manager.store_with_edrr_phase(
            {"from_phase": self.current_phase.value if self.current_phase else None,
             "to_phase": phase.value,
             "timestamp": datetime.now().isoformat(),
             "task_id": self.task.get("id")},
            "PHASE_TRANSITION",
            phase.value,
            metadata={"cycle_id": self.cycle_id}
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
        
        logger.info(f"Progressed to {phase.value} phase for task: {self.task.get('description', 'Unknown')}")
    
    def _execute_expand_phase(self) -> None:
        """Execute the Expand phase of the EDRR cycle."""
        # Get prompt templates for the Expand phase
        templates = self.prompt_manager.list_templates(edrr_phase=Phase.EXPAND.value)
        
        # Retrieve relevant documentation
        docs = self.documentation_manager.query_documentation(
            self.task.get("description", ""),
            limit=5
        )
        
        # Analyze file structure if the task involves a file
        file_path = self.task.get("file_path")
        if file_path:
            analysis = self.code_analyzer.analyze_file(file_path)
        else:
            analysis = None
        
        # Instruct the WSDE team to brainstorm approaches
        approaches = self.wsde_team.build_consensus(
            {"id": self.task.get("id"),
             "description": self.task.get("description"),
             "documentation": docs,
             "analysis": analysis,
             "templates": templates}
        )
        
        # Store the results in memory
        self.results[Phase.EXPAND] = {
            "approaches": approaches,
            "documentation": docs,
            "analysis": analysis,
            "completed": True
        }
        
        self.memory_manager.store_with_edrr_phase(
            self.results[Phase.EXPAND],
            "RESULT",
            Phase.EXPAND.value,
            metadata={"cycle_id": self.cycle_id, "task_id": self.task.get("id")}
        )
    
    def _execute_differentiate_phase(self) -> None:
        """Execute the Differentiate phase of the EDRR cycle."""
        # Get prompt templates for the Differentiate phase
        templates = self.prompt_manager.list_templates(edrr_phase=Phase.DIFFERENTIATE.value)
        
        # Retrieve best practices documentation
        docs = self.documentation_manager.query_documentation(
            f"best practices {self.task.get('description', '')}",
            limit=5
        )
        
        # Get the approaches from the Expand phase
        expand_results = self.results.get(Phase.EXPAND, {})
        approaches = expand_results.get("approaches", [])
        
        # Evaluate code quality if there's code to evaluate
        code_to_evaluate = self.task.get("code")
        if code_to_evaluate:
            quality_analysis = self.code_analyzer.analyze_code(code_to_evaluate)
        else:
            quality_analysis = None
        
        # Instruct the WSDE team to evaluate and compare approaches
        evaluation = self.wsde_team.apply_enhanced_dialectical_reasoning_multi(
            {"id": self.task.get("id"),
             "description": self.task.get("description"),
             "approaches": approaches,
             "documentation": docs,
             "quality_analysis": quality_analysis,
             "templates": templates}
        )
        
        # Store the results in memory
        self.results[Phase.DIFFERENTIATE] = {
            "evaluation": evaluation,
            "documentation": docs,
            "quality_analysis": quality_analysis,
            "completed": True
        }
        
        self.memory_manager.store_with_edrr_phase(
            self.results[Phase.DIFFERENTIATE],
            "RESULT",
            Phase.DIFFERENTIATE.value,
            metadata={"cycle_id": self.cycle_id, "task_id": self.task.get("id")}
        )
    
    def _execute_refine_phase(self) -> None:
        """Execute the Refine phase of the EDRR cycle."""
        # Get prompt templates for the Refine phase
        templates = self.prompt_manager.list_templates(edrr_phase=Phase.REFINE.value)
        
        # Retrieve implementation examples
        docs = self.documentation_manager.query_documentation(
            f"implementation examples {self.task.get('description', '')}",
            limit=5
        )
        
        # Get the evaluation from the Differentiate phase
        differentiate_results = self.results.get(Phase.DIFFERENTIATE, {})
        evaluation = differentiate_results.get("evaluation", {})
        
        # Apply code transformations if needed
        code_to_transform = evaluation.get("selected_approach", {}).get("code")
        if code_to_transform:
            # This is a simplified example - in a real implementation, we would
            # determine what transformations to apply based on the evaluation
            transformed_code = self.ast_transformer.rename_identifier(
                code_to_transform,
                "old_name",
                "new_name"
            )
        else:
            transformed_code = None
        
        # Instruct the WSDE team to implement the selected approach
        implementation = self.wsde_team.apply_enhanced_dialectical_reasoning(
            {"id": self.task.get("id"),
             "description": self.task.get("description"),
             "selected_approach": evaluation.get("selected_approach"),
             "documentation": docs,
             "transformed_code": transformed_code,
             "templates": templates}
        )
        
        # Store the results in memory
        self.results[Phase.REFINE] = {
            "implementation": implementation,
            "documentation": docs,
            "transformed_code": transformed_code,
            "completed": True
        }
        
        self.memory_manager.store_with_edrr_phase(
            self.results[Phase.REFINE],
            "RESULT",
            Phase.REFINE.value,
            metadata={"cycle_id": self.cycle_id, "task_id": self.task.get("id")}
        )
    
    def _execute_retrospect_phase(self) -> None:
        """Execute the Retrospect phase of the EDRR cycle."""
        # Get prompt templates for the Retrospect phase
        templates = self.prompt_manager.list_templates(edrr_phase=Phase.RETROSPECT.value)
        
        # Retrieve evaluation criteria
        docs = self.documentation_manager.query_documentation(
            f"evaluation criteria {self.task.get('description', '')}",
            limit=5
        )
        
        # Get the implementation from the Refine phase
        refine_results = self.results.get(Phase.REFINE, {})
        implementation = refine_results.get("implementation", {})
        
        # Verify code quality if there's code to verify
        code_to_verify = implementation.get("code")
        if code_to_verify:
            is_valid = self.ast_transformer.validate_syntax(code_to_verify)
        else:
            is_valid = None
        
        # Instruct the WSDE team to evaluate the implementation
        evaluation = self.wsde_team.apply_dialectical_reasoning(
            {"id": self.task.get("id"),
             "description": self.task.get("description"),
             "implementation": implementation,
             "documentation": docs,
             "is_valid": is_valid,
             "templates": templates}
        )
        
        # Store the results in memory
        self.results[Phase.RETROSPECT] = {
            "evaluation": evaluation,
            "documentation": docs,
            "is_valid": is_valid,
            "completed": True
        }
        
        self.memory_manager.store_with_edrr_phase(
            self.results[Phase.RETROSPECT],
            "RESULT",
            Phase.RETROSPECT.value,
            metadata={"cycle_id": self.cycle_id, "task_id": self.task.get("id")}
        )
        
        # Generate a final report
        self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a final report summarizing the entire EDRR cycle.
        
        Returns:
            A dictionary containing the report
        """
        report = {
            "task": self.task,
            "cycle_id": self.cycle_id,
            "timestamp": datetime.now().isoformat(),
            "phases": {
                Phase.EXPAND.value: self.results.get(Phase.EXPAND, {}),
                Phase.DIFFERENTIATE.value: self.results.get(Phase.DIFFERENTIATE, {}),
                Phase.REFINE.value: self.results.get(Phase.REFINE, {}),
                Phase.RETROSPECT.value: self.results.get(Phase.RETROSPECT, {})
            },
            "summary": {
                "approaches_count": len(self.results.get(Phase.EXPAND, {}).get("approaches", [])),
                "selected_approach": self.results.get(Phase.DIFFERENTIATE, {}).get("evaluation", {}).get("selected_approach", {}),
                "implementation_success": self.results.get(Phase.RETROSPECT, {}).get("is_valid", False),
                "final_evaluation": self.results.get(Phase.RETROSPECT, {}).get("evaluation", {})
            }
        }
        
        # Store the report in memory
        self.memory_manager.store_with_edrr_phase(
            report,
            "REPORT",
            "report",
            metadata={"cycle_id": self.cycle_id, "task_id": self.task.get("id")}
        )
        
        logger.info(f"Generated final report for task: {self.task.get('description', 'Unknown')}")
        return report