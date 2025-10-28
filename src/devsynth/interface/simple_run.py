from __future__ import annotations

"""Simple workflow execution using :class:`UXBridge`."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from devsynth.core.workflows import execute_command
from devsynth.interface.ux_bridge import UXBridge


@dataclass
class WorkflowResult:
    """Result returned from :func:`run_workflow`."""

    summary: str


def run_workflow(bridge: UXBridge) -> dict[str, Any] | None:
    """Run a workflow selected via ``bridge``.

    This mirrors the pseudocode in ``docs/implementation/uxbridge_interaction_pseudocode.md``.
    The user is asked which command to run and whether to execute it. The chosen
    command is then executed via :func:`devsynth.core.workflows.execute_command`.
    The command's summary is displayed through the bridge.
    """

    task = bridge.ask_question("What task should DevSynth run?")
    if not bridge.confirm_choice(f"Run {task} now?"):
        return None

    result = execute_command(task, {})
    summary = str(result.get("summary", result))
    bridge.display_result(summary)
    return result
