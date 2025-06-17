"""Wrapper functions for executing workflows."""

from typing import Any, Dict

from devsynth.application.orchestration.workflow import workflow_manager


def execute_command(command: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a workflow command through the application workflow manager."""
    return workflow_manager.execute_command(command, args)


def filter_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of ``args`` without ``None`` values."""
    return {k: v for k, v in args.items() if v is not None}


def init_project(**kwargs: Any) -> Dict[str, Any]:
    """Initialize a new project."""
    return execute_command("init", filter_args(kwargs))


def generate_specs(requirements_file: str) -> Dict[str, Any]:
    """Generate specifications from a requirements file."""
    return execute_command("spec", {"requirements_file": requirements_file})


def generate_tests(spec_file: str) -> Dict[str, Any]:
    """Generate tests from specs."""
    return execute_command("test", {"spec_file": spec_file})


def generate_code() -> Dict[str, Any]:
    """Generate implementation code from tests."""
    return execute_command("code", {})


def run_pipeline(target: str | None = None) -> Dict[str, Any]:
    """Execute the generated code or a specific target."""
    return execute_command("run-pipeline", filter_args({"target": target}))


def update_config(
    key: str | None = None, value: str | None = None, *, list_models: bool = False
) -> Dict[str, Any]:
    """View or set configuration options."""
    args = filter_args({"key": key, "value": value})
    if list_models:
        args["list_models"] = True
    return execute_command("config", args)


def inspect_requirements(
    input: str | None = None, *, interactive: bool = False
) -> Dict[str, Any]:
    """Inspect requirements interactively or from a file."""
    return execute_command(
        "inspect", filter_args({"input": input, "interactive": interactive})
    )
