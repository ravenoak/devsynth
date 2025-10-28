"""
Refactor Workflow Engine for DevSynth.

This module provides an enhanced workflow engine that can adapt to projects
in any state, detect the current project state automatically, and suggest
appropriate next steps.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

from ...application.code_analysis.project_state_analyzer import ProjectStateAnalyzer
from ...domain.models.workflow import Workflow, WorkflowStatus, WorkflowStep
from .workflow import WorkflowManager


class RefactorWorkflowManager:
    """
    Enhanced workflow manager with refactor capabilities.

    This class extends the standard workflow manager to handle projects in any state,
    detect the current project state automatically, and suggest appropriate next steps.
    """

    def __init__(self):
        """Initialize the refactor workflow manager."""
        self.workflow_manager = WorkflowManager()

    def analyze_project_state(self, project_path: str) -> dict[str, Any]:
        """
        Analyze the current state of the project.

        Args:
            project_path: Path to the project root directory

        Returns:
            A dictionary containing the analysis results
        """
        logger.info(f"Analyzing project state for {project_path}")

        # Create a project state analyzer
        analyzer = ProjectStateAnalyzer(project_path)

        # Analyze the project
        analysis = analyzer.analyze()

        # Merge health report fields at the top level for backward compatibility
        health_report = analysis.get("health_report", {})
        merged = {
            **analysis,
            **health_report,
        }
        return merged

    def determine_optimal_workflow(self, project_state: dict[str, Any]) -> str:
        """
        Determine the optimal workflow based on the project state.

        Args:
            project_state: The current state of the project

        Returns:
            The name of the optimal workflow
        """
        logger.info("Determining optimal workflow")

        # Check if the project has requirements
        has_requirements = project_state["requirements_count"] > 0

        # Check if the project has specifications
        has_specifications = project_state["specifications_count"] > 0

        # Check if the project has tests
        has_tests = project_state["test_count"] > 0

        # Check if the project has code
        has_code = project_state["code_count"] > 0

        # Determine the optimal workflow based on the project state
        if not has_requirements:
            return "requirements"
        if not has_specifications:
            return "specifications"
        if not has_tests:
            return "tests"
        if not has_code:
            return "code"

        # If all artifacts exist, return complete
        return "complete"

    def determine_entry_point(
        self, project_state: dict[str, Any], workflow: str
    ) -> str:
        """
        Determine the entry point for the workflow based on the project state.

        Args:
            project_state: The current state of the project
            workflow: The name of the workflow

        Returns:
            The name of the entry point
        """
        logger.info(f"Determining entry point for {workflow} workflow")

        if workflow == "requirements":
            return "inspect"
        elif workflow == "specifications":
            return "spec"
        elif workflow == "tests":
            return "test"
        elif workflow == "code":
            return "code"
        else:
            return "inspect"

    def suggest_next_steps(self, project_path: str) -> list[dict[str, Any]]:
        """
        Suggest next steps based on the current project state.

        Args:
            project_path: Path to the project root directory

        Returns:
            A list of suggested next steps
        """
        logger.info(f"Suggesting next steps for {project_path}")

        # Analyze the project state
        project_state = self.analyze_project_state(project_path)

        # Determine the optimal workflow
        workflow = self.determine_optimal_workflow(project_state)

        # Determine the entry point
        entry_point = self.determine_entry_point(project_state, workflow)

        # Generate suggestions based on the project state
        suggestions = []

        # Check for missing requirements
        if project_state["requirements_count"] == 0:
            suggestions.append(
                {
                    "command": "analyze",
                    "description": "Create requirements documentation to define project goals",
                    "priority": "high",
                }
            )

        # Check for missing specifications
        if project_state["specifications_count"] == 0:
            suggestions.append(
                {
                    "command": "spec",
                    "description": "Generate specifications from requirements",
                    "priority": (
                        "high" if project_state["requirements_count"] > 0 else "medium"
                    ),
                }
            )

        # Check for missing tests
        if project_state["test_count"] == 0:
            suggestions.append(
                {
                    "command": "test",
                    "description": "Generate tests from specifications",
                    "priority": (
                        "high"
                        if project_state["specifications_count"] > 0
                        else "medium"
                    ),
                }
            )

        # Check for missing code
        if project_state["code_count"] == 0:
            suggestions.append(
                {
                    "command": "code",
                    "description": "Generate code from tests",
                    "priority": "high" if project_state["test_count"] > 0 else "medium",
                }
            )

        # Check for unmatched requirements
        if project_state["requirements_spec_alignment"]["unmatched_requirements"]:
            suggestions.append(
                {
                    "command": "spec",
                    "description": f"Update specifications to address {len(project_state['requirements_spec_alignment']['unmatched_requirements'])} unmatched requirements",
                    "priority": "medium",
                }
            )

        # Check for unimplemented specifications
        if project_state["spec_code_alignment"]["unimplemented_specifications"]:
            suggestions.append(
                {
                    "command": "code",
                    "description": f"Implement code for {len(project_state['spec_code_alignment']['unimplemented_specifications'])} unimplemented specifications",
                    "priority": "medium",
                }
            )

        return suggestions

    def initialize_workflow(
        self, project_path: str
    ) -> tuple[str, str, list[dict[str, Any]]]:
        """
        Initialize a workflow based on the current project state.

        Args:
            project_path: Path to the project root directory

        Returns:
            A tuple containing the workflow name, entry point, and suggested next steps
        """
        logger.info(f"Initializing workflow for {project_path}")

        # Analyze the project state
        project_state = self.analyze_project_state(project_path)

        # Determine the optimal workflow
        workflow = self.determine_optimal_workflow(project_state)

        # Determine the entry point
        entry_point = self.determine_entry_point(project_state, workflow)

        # Generate suggestions
        suggestions = self.suggest_next_steps(project_path)

        return workflow, entry_point, suggestions

    def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a command with the standard workflow manager.

        Args:
            command: The command to execute
            args: The arguments for the command

        Returns:
            The result of the command execution
        """
        logger.info(f"Executing command: {command}")

        # Execute the command with the standard workflow manager
        result = self.workflow_manager.execute_command(command, args)

        # If the command was successful, analyze the project state and suggest next steps
        if result.get("success", False):
            project_path = args.get("path", os.getcwd())
            suggestions = self.suggest_next_steps(project_path)
            result["suggestions"] = suggestions

        return result

    def execute_refactor_workflow(
        self, project_path: str, max_steps: int = 3
    ) -> dict[str, Any]:
        """
        Execute a refactor workflow based on the current project state.

        This method executes a multi-step workflow that adapts based on the project state.
        It will execute up to max_steps commands, analyzing the project state after each step
        and determining the next command to execute based on the updated state.

        Args:
            project_path: Path to the project root directory
            max_steps: Maximum number of steps to execute (default: 3)

        Returns:
            The result of the workflow execution, including:
            - status: "success" or "error"
            - steps: List of steps executed
            - workflow: The name of the workflow
            - entry_point: The initial entry point
            - suggestions: Suggestions for next steps
            - final_state: Summary of the final project state
        """
        logger.info(
            f"Executing refactor workflow for {project_path} with max_steps={max_steps}"
        )

        # Initialize the workflow
        workflow, entry_point, suggestions = self.initialize_workflow(project_path)

        # Initialize result tracking
        result = {
            "status": "success",
            "success": True,
            "message": "Workflow executed successfully",
            "steps": [],
            "workflow": workflow,
            "entry_point": entry_point,
            "initial_suggestions": suggestions,
        }

        # Execute up to max_steps commands
        current_command = entry_point
        for step in range(max_steps):
            logger.info(f"Executing step {step + 1}/{max_steps}: {current_command}")

            # Execute the current command
            step_result = self.execute_command(current_command, {"path": project_path})

            # Record the step
            result["steps"].append(
                {
                    "command": current_command,
                    "status": (
                        "success" if step_result.get("success", False) else "error"
                    ),
                    "details": step_result,
                }
            )

            # If the command failed, stop the workflow
            if not step_result.get("success", False):
                result["status"] = "error"
                result["success"] = False
                result["error_message"] = step_result.get(
                    "message", f"Command {current_command} failed"
                )
                break

            # Analyze the project state after the command execution
            project_state = self.analyze_project_state(project_path)

            # Determine if we need to continue
            if self.determine_optimal_workflow(project_state) == "complete":
                logger.info("Workflow complete, no further steps needed")
                break

            # Get suggestions for next steps
            suggestions = self.suggest_next_steps(project_path)

            # If there are no suggestions, we're done
            if not suggestions:
                logger.info("No further suggestions, workflow complete")
                break

            # Get the highest priority suggestion
            next_suggestion = sorted(
                suggestions,
                key=lambda s: (
                    0
                    if s.get("priority") == "high"
                    else 1 if s.get("priority") == "medium" else 2
                ),
            )[0]

            # Set the next command
            current_command = next_suggestion["command"]

            # If we've reached the last step, break
            if step == max_steps - 1:
                logger.info(f"Reached maximum steps ({max_steps}), stopping workflow")
                break

        # Analyze the final project state
        final_state = self.analyze_project_state(project_path)

        # Add final information to the result
        result["final_state"] = {
            "requirements_count": final_state["requirements_count"],
            "specifications_count": final_state["specifications_count"],
            "test_count": final_state["test_count"],
            "code_count": final_state["code_count"],
            "requirements_spec_alignment": final_state["requirements_spec_alignment"][
                "alignment_score"
            ],
            "spec_code_alignment": final_state["spec_code_alignment"][
                "implementation_score"
            ],
        }
        result["suggestions"] = self.suggest_next_steps(project_path)

        return result


# Create a singleton instance of the refactor workflow manager
refactor_workflow_manager = RefactorWorkflowManager()
