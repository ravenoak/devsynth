"""Wrapper functions and utilities for executing workflows."""

from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import Optional, TypeAlias, Union

import yaml

from devsynth.agents.critique_agent import CritiqueAgent
from devsynth.config import get_project_config, save_config
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | Sequence["JSONValue"] | Mapping[str, "JSONValue"]
MutableJSONMapping: TypeAlias = MutableMapping[str, JSONValue]


def _get_workflow_manager():
    """Return the global ``WorkflowManager`` instance lazily."""
    from devsynth.application.orchestration.workflow import workflow_manager

    return workflow_manager


# Expose the singleton so it can be imported directly from this module.
# Importing the application workflow may require optional dependencies, so we
# fall back to ``None`` when they are unavailable.
try:  # pragma: no cover - defensive import
    workflow_manager = _get_workflow_manager()
except Exception:  # pragma: no cover
    workflow_manager = None


def execute_command(command: str, args: MutableJSONMapping) -> MutableJSONMapping:
    """Execute a workflow command through the application workflow manager."""
    return _get_workflow_manager().execute_command(command, args)


def filter_args(args: Mapping[str, JSONValue]) -> dict[str, JSONValue]:
    """Return a copy of ``args`` without ``None`` values."""
    return {k: v for k, v in args.items() if v is not None}


def _review_content(content: str, bridge: UXBridge | None = None):
    """Run :class:`CritiqueAgent` on ``content`` and surface issues."""

    critic = CritiqueAgent()
    critique = critic.review(content)
    if critique.issues:
        logger.warning("Critique issues: %s", "; ".join(critique.issues))
        if bridge:
            bridge.display_result(
                "[red]Critique issues:\n" + "\n".join(critique.issues) + "[/red]"
            )
    else:
        logger.info("Critique passed with no issues.")
        if bridge:
            bridge.display_result("[green]Critique passed with no issues.[/green]")
    return critique


def init_project(**kwargs: JSONValue) -> MutableJSONMapping:
    """Initialize a new project."""
    return execute_command("init", filter_args(kwargs))


def generate_specs(requirements_file: str) -> MutableJSONMapping:
    """Generate specifications from a requirements file."""
    return execute_command("spec", {"requirements_file": requirements_file})


def generate_tests(
    spec_file: str, *, bridge: UXBridge | None = None
) -> MutableJSONMapping:
    """Generate tests from specs and run a critique pass."""

    result = execute_command("test", {"spec_file": spec_file})
    content = result.get("content")
    if isinstance(content, str):
        critique = _review_content(content, bridge)
        result["critique"] = critique.issues
        result["critique_approved"] = critique.approved
    return result


def generate_code(*, bridge: UXBridge | None = None) -> MutableJSONMapping:
    """Generate implementation code from tests and critique it."""

    empty_payload: dict[str, JSONValue] = {}
    result = execute_command("code", empty_payload)
    content = result.get("content")
    if isinstance(content, str):
        critique = _review_content(content, bridge)
        result["critique"] = critique.issues
        result["critique_approved"] = critique.approved
    return result


def run_pipeline(
    target: str | None = None, report: Mapping[str, JSONValue] | None = None
) -> MutableJSONMapping:
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
    key: str | None = None,
    value: str | None = None,
    *,
    list_models: bool = False,
) -> MutableJSONMapping:
    """View or set configuration options."""
    args = filter_args({"key": key, "value": value})
    if list_models:
        args["list_models"] = True
    return execute_command("config", args)


def inspect_requirements(
    input: str | None = None, *, interactive: bool = False
) -> MutableJSONMapping:
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
    # Persist to .devsynth/project.yaml regardless of pyproject presence.
    save_config(cfg, use_pyproject=False)

    bridge.display_result(f"[green]Requirements saved to {output_file}[/green]")
