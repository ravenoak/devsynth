"""Interactive requirements wizard for the CLI.

This module provides a simplified interface for collecting a single
requirement from the user. It mirrors the behaviour of the Typer based
``wizard`` command while remaining easy to invoke directly in tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

from devsynth.config.settings import ensure_path_exists
from devsynth.domain.models.requirement import RequirementPriority, RequirementType
from devsynth.interface.ux_bridge import UXBridge

from .config import CLIConfig


def requirements_wizard(
    bridge: UXBridge,
    *,
    output_file: str = "requirements_wizard.json",
    title: Optional[str] = None,
    description: Optional[str] = None,
    req_type: Optional[str] = None,
    priority: Optional[str] = None,
    constraints: Optional[str] = None,
    config: Optional[CLIConfig] = None,
) -> None:
    """Collect requirement details via ``bridge`` and persist them.

    Parameters
    ----------
    bridge:
        Interface used to ask questions and display results.
    output_file:
        Path where the requirement should be written. The file is always JSON.
    title, description, req_type, priority, constraints:
        Optional values to pre-populate the wizard. When ``config.non_interactive``
        is true these values are used directly without prompting.
    """

    config = config or CLIConfig.from_env()

    steps: Sequence[tuple[str, str, Optional[Sequence[str]], str]] = [
        ("title", "Requirement title", None, ""),
        ("description", "Requirement description", None, ""),
        (
            "type",
            "Requirement type",
            [t.value for t in RequirementType],
            RequirementType.FUNCTIONAL.value,
        ),
        (
            "priority",
            "Requirement priority",
            [p.value for p in RequirementPriority],
            RequirementPriority.MEDIUM.value,
        ),
        ("constraints", "Constraints (comma separated, optional)", None, ""),
    ]

    # Seed responses with any provided values so they act as defaults when
    # prompting or allow fully non-interactive operation.
    responses: dict[str, str] = {}
    if title is not None:
        responses["title"] = title
    if description is not None:
        responses["description"] = description
    if req_type is not None:
        responses["type"] = req_type
    if priority is not None:
        responses["priority"] = priority
    if constraints is not None:
        responses["constraints"] = constraints

    index = 0
    while index < len(steps):
        key, message, choices, default = steps[index]
        default_val = responses.get(key, default)
        if config.non_interactive:
            reply = default_val or ""
        else:
            prefix = f"Step {index + 1}/{len(steps)}: "
            reply = bridge.ask_question(
                prefix + message + " (type 'back' to go back)",
                choices=choices,
                default=default_val,
            )
        if reply.lower() == "back":
            if index > 0:
                index -= 1
            else:
                bridge.display_result("[yellow]Already at first step.[/yellow]")
            continue
        responses[key] = reply
        index += 1

    result = {
        "title": responses.get("title", ""),
        "description": responses.get("description", ""),
        "type": responses.get("type", RequirementType.FUNCTIONAL.value),
        # Priority should always reflect the last user choice. We rely on the
        # responses dictionary so that navigation doesn't discard the value.
        "priority": responses.get("priority", RequirementPriority.MEDIUM.value),
        "constraints": [
            c.strip() for c in responses.get("constraints", "").split(",") if c.strip()
        ],
    }

    path = Path(output_file)
    out_dir = ensure_path_exists(str(path.parent), create=True)
    output_path = Path(out_dir) / path.name
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    bridge.display_result(f"[green]Requirements saved to {output_path}[/green]")


__all__ = ["requirements_wizard"]
