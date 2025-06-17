"""Wrapper functions for executing workflows."""

from typing import Any, Dict

from devsynth.application.orchestration.workflow import workflow_manager


def execute_command(command: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a workflow command through the application workflow manager."""
    return workflow_manager.execute_command(command, args)
