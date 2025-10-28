"""Interactive requirements wizard shared by CLI and other interfaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from collections.abc import Sequence

from devsynth.application.cli.config import CLIConfig
from devsynth.application.wizard_textual import (
    TextualWizardViewModel,
    is_back_command,
)
from devsynth.config import get_project_config, save_config
from devsynth.config.settings import ensure_path_exists
from devsynth.domain.models.requirement import RequirementPriority, RequirementType
from devsynth.interface.ux_bridge import UXBridge
from devsynth.utils.logging import DevSynthLogger

REQUIREMENTS_HELP: dict[str, str] = {
    "title": "Provide a concise, descriptive name for the requirement.",
    "description": "Explain what the system should accomplish in clear terms.",
    "type": "Choose whether the requirement is functional or non-functional.",
    "priority": "Select how important the requirement is relative to others.",
    "constraints": (
        "List any limitations or conditions separated by commas, such as"
        " tooling, performance thresholds, or compliance needs."
    ),
}


def requirements_wizard(
    bridge: UXBridge,
    *,
    output_file: str = "requirements_wizard.json",
    title: str | None = None,
    description: str | None = None,
    req_type: str | None = None,
    priority: str | None = None,
    constraints: str | None = None,
    config: CLIConfig | None = None,
) -> None:
    """Collect requirement details via ``bridge`` and persist them.

    The wizard preserves responses between steps so navigation does not discard
    user input. Priority values are always taken from the most recent user
    choice to ensure they persist even when users move backwards through the
    wizard.
    """

    config = config or CLIConfig.from_env()
    logger = DevSynthLogger(__name__)
    capabilities = dict(getattr(bridge, "capabilities", {}) or {})
    supports_layout = bool(capabilities.get("supports_layout_panels"))
    supports_shortcuts = bool(capabilities.get("supports_keyboard_shortcuts"))
    textual_view: TextualWizardViewModel | None = None
    if supports_layout:
        textual_view = TextualWizardViewModel(
            bridge,
            steps=[
                "Title",
                "Description",
                "Type",
                "Priority",
                "Constraints",
            ],
            contextual_help=REQUIREMENTS_HELP,
            keyboard_shortcuts=supports_shortcuts,
        )
        textual_view.set_active_step(0)

    steps: Sequence[tuple[str, str, Sequence[str] | None, str]] = [
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
        if textual_view is not None:
            textual_view.set_active_step(index)
            textual_view.present_question(
                key,
                f"Step {index + 1}/{len(steps)}: {message}",
                help_text=REQUIREMENTS_HELP.get(key),
            )
        if config.non_interactive:
            reply = default_val or ""
        else:
            prefix = f"Step {index + 1}/{len(steps)}: "
            nav_hint = (
                " (use ← to go back)"
                if supports_shortcuts and textual_view is not None
                else " (type 'back' to go back)"
            )
            reply = bridge.ask_question(
                prefix + message + nav_hint,
                choices=choices,
                default=default_val,
            )
        if is_back_command(str(reply), keyboard_shortcuts=supports_shortcuts):
            if index > 0:
                index -= 1
            else:
                bridge.display_result("[yellow]Already at first step.[/yellow]")
            continue
        responses[key] = reply
        logger.info("wizard_step", step=key, value=reply)
        if textual_view is not None:
            textual_view.record_field(key, message, reply)
            textual_view.log_progress(f"Captured {message}")
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

    summary_lines = [
        f"Title: {result['title']}",
        f"Type: {result['type']}",
        f"Priority: {result['priority']}",
        "Constraints: "
        + (", ".join(result["constraints"]) if result["constraints"] else "—"),
    ]
    if textual_view is not None:
        textual_view.set_summary_lines(summary_lines)
        textual_view.record_activity(f"Saved requirements to {output_path}")

    bridge.display_result(f"[green]Requirements saved to {output_path}[/green]")


__all__ = ["requirements_wizard"]
