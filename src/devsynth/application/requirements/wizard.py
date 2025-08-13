"""Interactive requirements wizard shared by CLI and other interfaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

from devsynth.application.cli.config import CLIConfig
from devsynth.config import get_project_config, save_config
from devsynth.config.settings import ensure_path_exists
from devsynth.domain.models.requirement import RequirementPriority, RequirementType
from devsynth.interface.ux_bridge import UXBridge
from devsynth.utils.logging import DevSynthLogger


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

    The wizard preserves responses between steps so navigation does not discard
    user input. Priority values are always taken from the most recent user
    choice to ensure they persist even when users move backwards through the
    wizard.
    """

    config = config or CLIConfig.from_env()
    logger = DevSynthLogger(__name__)

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

    # Seed with defaults so navigating backwards preserves earlier answers.
    responses: dict[str, str] = {key: (default or "") for key, _, _, default in steps}
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
        logger.info("wizard_step", step=key, value=reply)
        index += 1

    result = {
        "title": responses.get("title", ""),
        "description": responses.get("description", ""),
        "type": responses.get("type", RequirementType.FUNCTIONAL.value),
        # Priority should always reflect the last user choice.
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

    cfg = get_project_config(Path("."))
    cfg.priority = responses.get("priority", RequirementPriority.MEDIUM.value)
    cfg.constraints = responses.get("constraints", "")
    # Always persist to .devsynth/project.yaml to mirror gather flows.
    try:
        save_config(cfg, use_pyproject=False)
        logger.info("requirements_saved", priority=cfg.priority)
    except Exception as exc:  # pragma: no cover - unexpected
        logger.error("requirements_save_failed", exc_info=exc)
        raise

    bridge.display_result(f"[green]Requirements saved to {output_path}[/green]")


__all__ = ["requirements_wizard"]
