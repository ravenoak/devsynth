"""Wrapper functions and utilities for executing workflows."""

from typing import Any, Dict
from pathlib import Path
import json
import yaml

from devsynth.application.orchestration.workflow import workflow_manager
from devsynth.interface.ux_bridge import UXBridge
from devsynth.config import get_project_config, save_config


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


def run_pipeline(target: str | None = None, report: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Execute the generated code or a specific target.

    Parameters
    ----------
    target:
        Specific execution target such as ``unit-tests``.
    report:
        Optional report data to persist alongside pipeline results.
    """

    return execute_command(
        "run-pipeline",
        filter_args({"target": target, "report": report}),
    )


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


def gather_requirements(
    bridge: UXBridge,
    *,
    output_file: str = ".devsynth/requirements.json",
) -> None:
    """Interactively collect project goals, constraints and priority.

    Parameters
    ----------
    bridge:
        Interface used for user interaction.
    output_file:
        File where gathered requirements should be written. The extension
        determines whether JSON or YAML will be used.
    """

    goals = bridge.prompt("Project goals (comma separated)")
    constraints = bridge.prompt("Project constraints (comma separated)")
    priority = bridge.prompt(
        "Overall priority",
        choices=["low", "medium", "high"],
        default="medium",
    )
    if not bridge.confirm(f"Save requirements to {output_file}?"):
        bridge.display_result("[yellow]Requirements not saved.[/yellow]")
        return

    data = {
        "goals": [g.strip() for g in goals.split(",") if g.strip()],
        "constraints": [c.strip() for c in constraints.split(",") if c.strip()],
        "priority": priority,
    }

    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if path.suffix == ".json":
            json.dump(data, f, indent=2)
        else:
            yaml.safe_dump(data, f, sort_keys=False)

    cfg = get_project_config(Path("."))
    cfg.goals = goals
    cfg.constraints = constraints
    if hasattr(cfg, "priority"):
        setattr(cfg, "priority", priority)
    save_config(cfg, use_pyproject=(Path("pyproject.toml").exists()))

    bridge.display_result(f"[green]Requirements saved to {output_file}[/green]")
