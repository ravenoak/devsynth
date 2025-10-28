"""
Workflow management system for DevSynth.
Coordinates between CLI and agent system, maintains project state,
and handles human intervention when needed.
"""

import os
from typing import Any, Dict, List, Optional
from collections.abc import Callable
from uuid import uuid4

from rich.console import Console
from rich.prompt import Prompt

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

from ...adapters.orchestration.langgraph_adapter import (
    FileSystemWorkflowRepository,
    LangGraphWorkflowEngine,
    NeedsHumanInterventionError,
)
from ...domain.models.workflow import Workflow, WorkflowStatus, WorkflowStep
from ...ports.orchestration_port import OrchestrationPort

console = Console()


class WorkflowManager:
    """Manages workflows for the DevSynth system."""

    def __init__(self, bridge: UXBridge = CLIUXBridge()):
        """Initialize the workflow manager."""
        self.bridge = bridge
        # Set up human intervention callback
        self.orchestration_port = OrchestrationPort(
            workflow_engine=LangGraphWorkflowEngine(
                human_intervention_callback=self._handle_human_intervention
            ),
            workflow_repository=FileSystemWorkflowRepository(),
        )

    def _handle_human_intervention(
        self, workflow_id: str, step_id: str, message: str
    ) -> str:
        """Handle human intervention requests."""
        self.bridge.display_result("[yellow]Human intervention required:[/yellow]")
        self.bridge.display_result(f"[bold]{message}[/bold]")
        response = self.bridge.ask_question("Your input")
        return response

    def _create_workflow_for_command(
        self, command: str, args: dict[str, Any]
    ) -> Workflow:
        """Create a workflow for a specific command."""
        workflow = self.orchestration_port.create_workflow(
            name=f"{command}-workflow-{uuid4().hex[:8]}",
            description=f"Workflow for {command} command",
        )

        # Add steps based on the command
        if command == "init":
            self._add_init_workflow_steps(workflow, args)
        elif command == "inspect":
            self._add_inspect_workflow_steps(workflow, args)
        elif command == "spec":
            self._add_spec_workflow_steps(workflow, args)
        elif command == "test":
            self._add_test_workflow_steps(workflow, args)
        elif command == "code":
            self._add_code_workflow_steps(workflow, args)
        elif command == "run":
            self._add_run_workflow_steps(workflow, args)
        elif command == "config":
            self._add_config_workflow_steps(workflow, args)

        return workflow

    def _add_inspect_workflow_steps(
        self, workflow: Workflow, args: dict[str, Any]
    ) -> None:
        """Add steps for the inspect command workflow."""
        if args.get("interactive"):
            # Step 1: Start interactive session
            self.orchestration_port.add_step(
                workflow,
                WorkflowStep(
                    id=f"start-interactive-{uuid4().hex[:8]}",
                    name="Start Interactive Session",
                    description="Start an interactive session for requirement gathering",
                    agent_type="requirement_analyzer",
                ),
            )

            # Step 2: Ask questions
            self.orchestration_port.add_step(
                workflow,
                WorkflowStep(
                    id=f"ask-questions-{uuid4().hex[:8]}",
                    name="Ask Questions",
                    description="Ask questions about requirements",
                    agent_type="requirement_analyzer",
                ),
            )
        else:
            # Step 1: Read requirements file
            self.orchestration_port.add_step(
                workflow,
                WorkflowStep(
                    id=f"read-requirements-{uuid4().hex[:8]}",
                    name="Read Requirements",
                    description="Read and parse the requirements file",
                    agent_type="document_reader",
                ),
            )

        # Step 3: Create structured representation
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"create-structure-{uuid4().hex[:8]}",
                name="Create Structured Representation",
                description="Create a structured representation of the requirements",
                agent_type="requirement_analyzer",
            ),
        )

        # Step 4: Generate summary
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"generate-summary-{uuid4().hex[:8]}",
                name="Generate Summary",
                description="Generate a summary of the requirements",
                agent_type="requirement_analyzer",
            ),
        )

    def _add_init_workflow_steps(
        self, workflow: Workflow, args: dict[str, Any]
    ) -> None:
        """Add steps for the init command workflow."""
        # Step 1: Validate project path
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"validate-path-{uuid4().hex[:8]}",
                name="Validate Project Path",
                description="Validate the project path and ensure it's suitable for initialization",
                agent_type="validator",
            ),
        )

        # Step 2: Create project structure
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"create-structure-{uuid4().hex[:8]}",
                name="Create Project Structure",
                description="Create the initial project directory structure",
                agent_type="file_system",
            ),
        )

        # Step 3: Initialize configuration
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"init-config-{uuid4().hex[:8]}",
                name="Initialize Configuration",
                description="Create initial configuration files",
                agent_type="config_manager",
            ),
        )

        # Step 4: Select memory backend
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"select-memory-{uuid4().hex[:8]}",
                name="Select Memory Backend",
                description="Choose persistent memory backend",
                agent_type="config_manager",
            ),
        )

        # Step 5: Configure optional features
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"set-features-{uuid4().hex[:8]}",
                name="Configure Features",
                description="Enable or disable optional features",
                agent_type="config_manager",
            ),
        )

        # Step 6: Offline mode selection
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"offline-mode-{uuid4().hex[:8]}",
                name="Set Offline Mode",
                description="Choose offline or online mode",
                agent_type="config_manager",
            ),
        )

    def _add_spec_workflow_steps(
        self, workflow: Workflow, args: dict[str, Any]
    ) -> None:
        """Add steps for the spec command workflow."""
        # Step 1: Read requirements
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"read-requirements-{uuid4().hex[:8]}",
                name="Read Requirements",
                description="Read and parse the requirements document",
                agent_type="document_reader",
            ),
        )

        # Step 2: Generate domain model
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"generate-domain-{uuid4().hex[:8]}",
                name="Generate Domain Model",
                description="Generate domain model from requirements",
                agent_type="domain_modeler",
            ),
        )

        # Step 3: Create specifications
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"create-specs-{uuid4().hex[:8]}",
                name="Create Specifications",
                description="Create detailed specifications document",
                agent_type="spec_writer",
            ),
        )

    def _add_test_workflow_steps(
        self, workflow: Workflow, args: dict[str, Any]
    ) -> None:
        """Add steps for the test command workflow."""
        # Step 1: Read specifications
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"read-specs-{uuid4().hex[:8]}",
                name="Read Specifications",
                description="Read and parse the specifications document",
                agent_type="document_reader",
            ),
        )

        # Step 2: Generate test cases
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"generate-test-cases-{uuid4().hex[:8]}",
                name="Generate Test Cases",
                description="Generate test cases from specifications",
                agent_type="test_designer",
            ),
        )

        # Step 3: Write test code
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"write-tests-{uuid4().hex[:8]}",
                name="Write Test Code",
                description="Write test code based on test cases",
                agent_type="test_coder",
            ),
        )

    def _add_code_workflow_steps(
        self, workflow: Workflow, args: dict[str, Any]
    ) -> None:
        """Add steps for the code command workflow."""
        # Step 1: Read tests
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"read-tests-{uuid4().hex[:8]}",
                name="Read Tests",
                description="Read and parse the test code",
                agent_type="code_reader",
            ),
        )

        # Step 2: Design implementation
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"design-implementation-{uuid4().hex[:8]}",
                name="Design Implementation",
                description="Design implementation to satisfy tests",
                agent_type="architect",
            ),
        )

        # Step 3: Write implementation code
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"write-code-{uuid4().hex[:8]}",
                name="Write Implementation Code",
                description="Write implementation code based on design",
                agent_type="coder",
            ),
        )

        # Step 4: Verify implementation
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"verify-code-{uuid4().hex[:8]}",
                name="Verify Implementation",
                description="Verify implementation against tests",
                agent_type="tester",
            ),
        )

    def _add_run_workflow_steps(self, workflow: Workflow, args: dict[str, Any]) -> None:
        """Add steps for the run command workflow."""
        # Step 1: Prepare environment
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"prepare-env-{uuid4().hex[:8]}",
                name="Prepare Environment",
                description="Prepare the execution environment",
                agent_type="environment_manager",
            ),
        )

        # Step 2: Execute code
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"execute-code-{uuid4().hex[:8]}",
                name="Execute Code",
                description="Execute the generated code",
                agent_type="executor",
            ),
        )

        # Step 3: Collect results
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"collect-results-{uuid4().hex[:8]}",
                name="Collect Results",
                description="Collect and format execution results",
                agent_type="result_collector",
            ),
        )

    def _add_config_workflow_steps(
        self, workflow: Workflow, args: dict[str, Any]
    ) -> None:
        """Add steps for the config command workflow."""
        # Step 1: Read configuration
        self.orchestration_port.add_step(
            workflow,
            WorkflowStep(
                id=f"read-config-{uuid4().hex[:8]}",
                name="Read Configuration",
                description="Read current configuration",
                agent_type="config_reader",
            ),
        )

        # If setting a value
        if args.get("key") and args.get("value"):
            # Step 2: Update configuration
            self.orchestration_port.add_step(
                workflow,
                WorkflowStep(
                    id=f"update-config-{uuid4().hex[:8]}",
                    name="Update Configuration",
                    description="Update configuration with new value",
                    agent_type="config_writer",
                ),
            )

    def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a command through the workflow system."""
        try:
            if command in {"edrr-cycle", "edrr_cycle"}:
                return self._execute_edrr_cycle(args)

            # Create context with command and arguments
            context = {
                "command": command,
                "project_root": args.get("path", os.getcwd()),
                **args,
            }

            # Create workflow for the command
            workflow = self._create_workflow_for_command(command, args)

            # Execute the workflow
            try:
                executed_workflow = self.orchestration_port.execute_workflow(
                    workflow_id=workflow.id, context=context
                )

                # Check if workflow was found and executed
                if executed_workflow is None:
                    return {
                        "success": False,
                        "message": f"Workflow not found: {workflow.id}",
                        "workflow_id": workflow.id,
                    }

                # Return result based on workflow status
                if executed_workflow.status == WorkflowStatus.COMPLETED:
                    return {
                        "success": True,
                        "message": "Command executed successfully",
                        "workflow_id": workflow.id,
                    }
                elif executed_workflow.status == WorkflowStatus.FAILED:
                    return {
                        "success": False,
                        "message": "Command failed",
                        "workflow_id": workflow.id,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Command status: {executed_workflow.status.value}",
                        "workflow_id": workflow.id,
                    }

            except NeedsHumanInterventionError as e:
                # Handle human intervention
                user_input = self._handle_human_intervention(
                    e.workflow_id, e.step_id, e.message
                )

                # Try executing the workflow again with the human input
                executed_workflow = self.orchestration_port.execute_workflow(
                    workflow_id=workflow.id,
                    context={**context, "human_input": user_input},
                )

                # Check if workflow was found and executed
                if executed_workflow is None:
                    return {
                        "success": False,
                        "message": f"Workflow not found after human intervention: {workflow.id}",
                        "workflow_id": workflow.id,
                    }

                return {
                    "success": True,
                    "message": "Command executed successfully after human intervention",
                    "workflow_id": workflow.id,
                }

        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """Get the status of a workflow."""
        return self.orchestration_port.get_workflow_status(workflow_id)

    def _execute_edrr_cycle(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate the provided manifest and start an EDRR cycle."""
        manifest = args.get("manifest")
        if not manifest or not os.path.exists(manifest):
            return {
                "success": False,
                "message": f"Manifest file not found: {manifest}",
            }

        try:
            import json
            from pathlib import Path

            json.loads(Path(manifest).read_text())
            return {"success": True, "message": "Starting EDRR cycle"}
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Manifest file not found: {manifest}",
            }
        except json.JSONDecodeError:
            return {"success": False, "message": f"Invalid manifest: {manifest}"}


# Create a singleton instance
workflow_manager = WorkflowManager()
